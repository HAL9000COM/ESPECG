#include <SPI.h>

#include <TFT_eSPI.h> // Hardware-specific library

#include <esp_adc_cal.h>
#include <SD.h>
#include <FS.h>

// Define custom pin
const int LO_P = 34;
const int LO_N = 35;

// Define ADC parameters
const int ADC_PIN = 33;                              // Analog input pin
const adc1_channel_t adcChannel = ADC1_CHANNEL_5;    // ADC channel
const adc_bits_width_t ADC_WIDTH = ADC_WIDTH_BIT_12; // ADC resolution
const adc_atten_t ADC_ATTEN = ADC_ATTEN_DB_11;       // ADC attenuation
esp_adc_cal_characteristics_t adcCal;

// Define SD card parameters
const int SD_CS = 26;
const int SD_FREQ = 4000000;

// Define timer interrupt parameters
const int SAMPLE_RATE = 200;                          // Sample rate in Hz (e.g., 1000 samples per second)
hw_timer_t *timer = NULL;                             // Timer object
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED; // Timer interrupt mutex

// Define interrupt buffer variables
#define BUFFER_SIZE 256

volatile int buffer[BUFFER_SIZE];
volatile bool newDataAvailable = false;
volatile uint8_t bufferIndex = 0;

// display variables
int x_count = 0;
int map_data_old = 0;

// logging variables
uint64_t sample_count = 0;
bool Lead_off = false;

TFT_eSPI tft = TFT_eSPI(); // Invoke custom library

void IRAM_ATTR onTimer()
{
  portENTER_CRITICAL_ISR(&timerMux);
  int data = adc1_get_raw(adcChannel);
  buffer[bufferIndex] = data;
  bufferIndex = (bufferIndex + 1) % BUFFER_SIZE;
  newDataAvailable = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}

File dataFile;

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
  adc1_config_channel_atten(adcChannel, ADC_ATTEN);

  // Configure timer interrupt
  timer = timerBegin(0, 80, true); // Timer 0, prescaler 80
  timerAttachInterrupt(timer, &onTimer, true);
  timerAlarmWrite(timer, 1000000 / SAMPLE_RATE, true); // Set the alarm to trigger at the desired sample rate (in microseconds)
  timerAlarmEnable(timer);

  // Calibrate ADC

  esp_adc_cal_value_t adcValue = esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN, ADC_WIDTH, ESP_ADC_CAL_VAL_EFUSE_VREF, &adcCal);
}

void loop()
{
  if (digitalRead(LO_P) == HIGH)
  {
    Serial.println("LA lead off");
    Lead_off = true;
  }
  else if (digitalRead(LO_N) == HIGH)
  {
    Serial.println("RA lead off");
    Lead_off = true;
  }
  else
  {
    Lead_off = false;
  }
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
      tft_update(localBuffer[i]);
      if (dataFile)
      {
        sd_write(readADCValue(localBuffer[i]));
      }
    }

    if (digitalRead(0) == LOW & dataFile)
    {
      Serial.println("Close File");
      closeSDFile();
    }
  }
}

void tft_update(int data)
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