// esp32 v2.0.17
#include <SPI.h>
#include <TFT_eSPI.h> // Hardware-specific library v2.5.43
#include <esp_adc_cal.h>
#include <SD.h>
#include <FS.h>

#include "ml_model.h"
#include <tflm_esp32.h>      //v1.0.0
#include <eloquent_tinyml.h> //v3.0.1

#define N_INPUTS 360
#define N_OUTPUTS 17
//  in future projects you may need to tweak this value: it's a trial and error process
#define ARENA_SIZE 80 * 1024

Eloquent::TF::Sequential<TF_NUM_OPS, ARENA_SIZE> tf;

// Define custom pin
const int LO_P = 34;
const int LO_N = 35;

// Define SD card parameters
const int SD_CS = 26;
const int SD_FREQ = 4000000;
File dataFile;

// display variables
int x_count = 0;
int map_data_old = 0;

// logging variables
uint64_t sample_count = 0;
bool lead_off = false;

// Define ADC parameters
const int ADC_PIN = 33;                              // Analog input pin
const int ref_PIN = 32;                              // Analog input pin
const adc1_channel_t ecgChannel = ADC1_CHANNEL_5;    // ADC channel
const adc1_channel_t refChannel = ADC1_CHANNEL_5;    // ADC channel
const adc_bits_width_t ADC_WIDTH = ADC_WIDTH_BIT_12; // ADC resolution
const adc_atten_t ADC_ATTEN = ADC_ATTEN_DB_12;       // ADC attenuation
esp_adc_cal_characteristics_t adcCal;
// #define CUSTOM_ADC // Comment this line to use the default ADC library

// Define timer interrupt parameters
const int SAMPLE_RATE = 200;                          // Sample rate in Hz (e.g., 1000 samples per second)
hw_timer_t *timer = NULL;                             // Timer object
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED; // Timer interrupt mutex

// Define interrupt buffer variables
#define BUFFER_SIZE 256

volatile int buffer[BUFFER_SIZE];
volatile bool newDataAvailable = false;
volatile uint8_t bufferIndex = 0;

class CircularBuffer
{
public:
  CircularBuffer(int size) : size_(size), buffer_(new int[size]), head_(0), tail_(0), count_(0) {}

  ~CircularBuffer()
  {
    delete[] buffer_;
  }

  void push(int data)
  {
    buffer_[head_] = data;
    head_ = (head_ + 1) % size_;
    if (count_ < size_)
    {
      count_++;
    }
    else
    {
      tail_ = (tail_ + 1) % size_;
    }
  }

  int *read()
  {
    int *data = new int[count_];
    for (int i = 0; i < count_; i++)
    {
      data[i] = buffer_[(tail_ + i) % size_];
    }
    return data;
  }

private:
  int size_;
  int *buffer_;
  int head_;
  int tail_;
  int count_;
};

CircularBuffer predictBuffer(N_INPUTS);

#ifdef CUSTOM_ADC
#include <soc/sens_reg.h>
#include <soc/sens_struct.h>
int IRAM_ATTR local_adc1_read(int channel)
{
  uint16_t adc_value;
  SENS.sar_meas_start1.sar1_en_pad = (1 << channel); // only one channel is selected
  while (SENS.sar_slave_addr1.meas_status != 0)
    ;
  SENS.sar_meas_start1.meas1_start_sar = 0;
  SENS.sar_meas_start1.meas1_start_sar = 1;
  while (SENS.sar_meas_start1.meas1_done_sar == 0)
    ;
  adc_value = SENS.sar_meas_start1.meas1_data_sar;
  return adc_value;
}

void IRAM_ATTR onTimer()
{
  portENTER_CRITICAL_ISR(&timerMux);
  int data = local_adc1_read(ecgChannel);
  buffer[bufferIndex] = data;
  bufferIndex = (bufferIndex + 1) % BUFFER_SIZE;
  newDataAvailable = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}
#else
void IRAM_ATTR onTimer()
{
  portENTER_CRITICAL_ISR(&timerMux);
  int data = adc1_get_raw(ecgChannel);
  buffer[bufferIndex] = data;
  bufferIndex = (bufferIndex + 1) % BUFFER_SIZE;
  newDataAvailable = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}
#endif

TFT_eSPI tft = TFT_eSPI(); // Invoke custom library

void setup()
{
  Serial.begin(115200);
  if (openSDFile())
  {
    // Write the CSV header
    dataFile.println("sample_count,data");
  }

  tft.init();
  tft.setRotation(3);
  tft.setTextSize(1);
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0, 0);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.println("ESP32 ECG");

  pinMode(LO_P, INPUT);
  pinMode(LO_N, INPUT);
  pinMode(ADC_PIN, INPUT);
  pinMode(0, INPUT);
  // Configure ADC
  adc1_config_width(ADC_WIDTH);
  adc1_config_channel_atten(ecgChannel, ADC_ATTEN);

  // Configure timer interrupt
  timer = timerBegin(0, 80, true); // Timer 0, prescaler 80
  timerAttachInterrupt(timer, &onTimer, true);
  timerAlarmWrite(timer, 1000000 / SAMPLE_RATE, true); // Set the alarm to trigger at the desired sample rate (in microseconds)
  timerAlarmEnable(timer);

  // Calibrate ADC
  esp_adc_cal_value_t adcValue = esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN, ADC_WIDTH, ESP_ADC_CAL_VAL_EFUSE_VREF, &adcCal);
  adc1_get_raw(ecgChannel);

  // check if model loaded fine
  while (!tf.begin(ml_model).isOk())
    Serial.println(tf.exception.toString());
}

void loop()
{

  lead_off_detect();

  // Process the data if new data is available
  if (newDataAvailable)
  {
    portENTER_CRITICAL_ISR(&timerMux);
    // Copy data from buffer for processing
    int localBuffer[BUFFER_SIZE];
    memcpy(localBuffer, (const void *)buffer, sizeof(buffer));
    newDataAvailable = false;
    int bufferIndex_old = bufferIndex;
    bufferIndex = 0;
    portEXIT_CRITICAL_ISR(&timerMux);
    // Process the data in localBuffer
    for (int i = 0; i < bufferIndex_old; i++)
    {
      sample_count++;
      tft_update_line(localBuffer[i]);
      predictBuffer.push(localBuffer[i]);
      if (dataFile)
      {
        sd_write(readADCValue(localBuffer[i]));
      }
    }

    // Make a prediction every time the buffer refreshes
    int prediction = predict();
    Serial.println(prediction);
  }

  // Close the file if the button is pressed
  if (digitalRead(0) == LOW & dataFile)
  {
    Serial.println("Close File");
    closeSDFile();
  }
}

bool lead_off_detect()
{
  if (digitalRead(LO_P) == HIGH)
  {
    // Serial.println("LA off");
    lead_off = true;
  }
  else if (digitalRead(LO_N) == HIGH)
  {
    // Serial.println("RA off");
    lead_off = true;
  }
  else
  {
    lead_off = false;
  }
  return lead_off
}

void tft_update_line(int data)
{
  if (x_count > 320)
  {
    x_count = 0;
  }
  // tft.setCursor(0, 8);
  // tft.setTextColor(TFT_YELLOW, TFT_RED);
  // tft.fillRect(0, 8, 320, 8, TFT_BLACK);
  int shift = 16;
  int map_data = map(data, 0, 4095, 200 + shift, 0 + shift);
  tft.fillRect(x_count, shift, 10, 201, TFT_BLACK);
  tft.drawLine(x_count - 1, map_data_old, x_count, map_data, TFT_GREEN);
  x_count++;
  map_data_old = map_data;
}

void sd_write(int data)
{
  // Open the CSV file in append mode
  // Check if the file was opened successfully
  if (dataFile)
  {
    // Write the data to the file with the timestamp
    dataFile.print(sample_count);
    dataFile.print(",");
    dataFile.println(data);
    // Close the file
    // Serial.println("Data written to data.csv");
  }
  else
  {
    // Serial.println("Error opening data.csv for writing!");
  }
}
bool openSDFile()
{
  if (!SD.begin(SD_CS, SPI, SD_FREQ))
  {
    Serial.println("SD card initialization failed!");
  }
  // Open the CSV file in append mode
  dataFile = SD.open("/data.csv", FILE_WRITE);
  // Check if the file was opened successfully
  if (!dataFile)
  {
    Serial.println("Error opening data.csv");
    return false;
  }
  return true;
}

bool closeSDFile()
{
  if (dataFile)
  {
    dataFile.close();
    return true;
  }
  SD.end();
  return false;
}

int readADCValue(uint32_t adc_raw)
{
  uint32_t voltage = esp_adc_cal_raw_to_voltage(adc_raw, &adcCal);
  return voltage;
}

int predict()
{
  int *raw_data = predictBuffer.read();
  float input[N_INPUTS]; // change type to float
  for (int i = 0; i < N_INPUTS; i++)
  {
    input[i] = static_cast<float>(raw_data[i]); // cast to float
  }

  while (!tf.predict(input).isOk())
    Serial.println(tf.exception.toString());
  Serial.print("Prediction: ");
  Serial.println(tf.classification);
}
