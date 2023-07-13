#include <SPI.h>

#include <TFT_eSPI.h> // Hardware-specific library

#include <esp_adc_cal.h>

// Define ADC parameters
const int ADC_PIN = 36;                              // Analog input pin
const adc_bits_width_t ADC_WIDTH = ADC_WIDTH_BIT_12; // ADC resolution
const adc_atten_t ADC_ATTEN = ADC_ATTEN_DB_11;       // ADC attenuation

// Define timer interrupt parameters
const int SAMPLE_RATE = 300;                          // Sample rate in Hz (e.g., 1000 samples per second)
hw_timer_t *timer = NULL;                             // Timer object
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED; // Timer interrupt mutex

// Define variables
volatile bool sampleReady = false;
volatile int raw_data = 0;

TFT_eSPI tft = TFT_eSPI(); // Invoke custom library
int x_count = 0;
int map_data_old = 0;

void IRAM_ATTR onTimer()
{
  portENTER_CRITICAL_ISR(&timerMux);
  sampleReady = true;
  raw_data = adc1_get_raw(ADC1_CHANNEL_0);
  portEXIT_CRITICAL_ISR(&timerMux);
}

void setup()
{
  Serial.begin(115200);
  tft.init();
  tft.setRotation(3);
  tft.setTextSize(1);
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0, 0);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.println("ESP32 ECG");
  pinMode(34, INPUT);
  pinMode(35, INPUT);
  pinMode(36, INPUT);
  // Configure ADC
  adc1_config_width(ADC_WIDTH);
  adc1_config_channel_atten(ADC1_CHANNEL_0, ADC_ATTEN);

  // Configure timer interrupt
  timer = timerBegin(0, 80, true); // Timer 0, prescaler 80
  timerAttachInterrupt(timer, &onTimer, true);
  timerAlarmWrite(timer, 1000000 / SAMPLE_RATE, true); // Set the alarm to trigger at the desired sample rate (in microseconds)
  timerAlarmEnable(timer);

  // Calibrate ADC
  esp_adc_cal_characteristics_t adcCal;
  esp_adc_cal_value_t adcValue = esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN, ADC_WIDTH, ESP_ADC_CAL_VAL_EFUSE_VREF, &adcCal);
}

void loop()
{
  unsigned long time_s = micros();
  tft.setCursor(0, 8);
  tft.setTextColor(TFT_YELLOW, TFT_RED);
  if (sampleReady)
  {

    if (x_count > 320)
    {
      x_count = 0;
    }
    if (digitalRead(34) == 0 || digitalRead(35) == 0)
    {
      if (digitalRead(34) == 0)
      {
        tft.print("LO+");
      }
      if (digitalRead(35) == 0)
      {
        tft.print("LO-");
      }
    }
    else
    {
      tft.fillRect(0, 8, 320, 8, TFT_BLACK);
    }
    portENTER_CRITICAL(&timerMux);
    sampleReady = false;
    portEXIT_CRITICAL(&timerMux);
    // int data = analogRead(36);
    int data = raw_data;
    int shift = 16;
    int map_data = map(data, 0, 4095, 0 + shift, 200 + shift);
    tft.fillRect(x_count, shift, 10, 201, TFT_BLACK);
    tft.drawLine(x_count - 1, map_data_old, x_count, map_data, TFT_GREEN);
    x_count++;
    map_data_old = map_data;
  }
  unsigned long time_e = micros();
  unsigned long exec_time = time_e - time_s+1;
  float fps = 1000000 / exec_time;
  tft.println(fps);
}