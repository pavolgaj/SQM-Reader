// setup for OLED1
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels

// Declaration for SSD1306 display connected using I2C
#define OLED_RESET 4
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);


#define LOGO_HEIGHT   16
#define LOGO_WIDTH    16

// setup for TSL2591
#include "SQM_TSL2591.h"
#include <Adafruit_AM2320.h>
#include <Adafruit_Sensor.h>

#define SEALEVELPRESSURE_HPA (1013.25)

#define PIN_T_SENSOR 12

SQM_TSL2591 sqm = SQM_TSL2591(2591);

void readSQM(void);

String PROTOCOL_NUMBER = "00000002";
String MODEL_NUMBER = "00000003";
String FEATURE_NUMBER = "00000001";
String SERIAL_NUMBER = "00000022";
String info;

String response;
bool new_data;

String temp_string;
float temp;

String c;

bool LED_ON = HIGH;
bool LED_OFF = LOW;

void setup_tsl() {
  pinMode(13, OUTPUT);
  if (sqm.begin()) {
    sqm.config.gain = TSL2591_GAIN_HIGH;
    sqm.config.time = TSL2591_INTEGRATIONTIME_200MS;
    sqm.configSensor();
    sqm.setCalibrationOffset(0.0);
    sqm.verbose = false;
  } else {
    Serial.println(F("SQM sensor not found"));
  }
  delay(1000);
}

// Setup temperature sensor.  This example uses the DHT22 sensor.
Adafruit_AM2320 am2320 = Adafruit_AM2320();
void setup_temperature() {
  bool status;
  // default settings
  am2320.begin();
}

float get_temperature() { return am2320.readTemperature(); }


void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LED_OFF);

  setup_temperature();

  setup_tsl(); 

  // SSD1306_SWITCHCAPVCC = generate display voltage from 3.3V internally
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  }

  // add a logo or other text for initialization
  // Show initial display buffer contents on the screen --
  // the library initializes this with an Adafruit splash screen.
  display.clearDisplay();
  display.setTextColor(WHITE);
  display.setTextSize(3);
  display.setCursor(40,6);
  display.print(F("DIY"));
  display.setCursor(40,34);
  display.print(F("SQM"));  
  display.display();
  delay(1000); // Pause for 1 second

  // Clear the buffer
  display.clearDisplay(); 

  pinMode(2,INPUT);  //spodne tlacitko
}

boolean meraj=true;
boolean show=true;

unsigned long start = 0;
int merajTlac=0;

void loop() {

  response = "";
  new_data = false;

  if (Serial.available() > 0) { 
    temp = get_temperature();
    sqm.takeReading();
    c = Serial.readString();
    if (c[1] == 'x') {
      if (c[0] == 'i') {
        response = String("i," + PROTOCOL_NUMBER + "," + MODEL_NUMBER +
                        "," + FEATURE_NUMBER + "," + SERIAL_NUMBER);
        new_data = true;
      }      
      if (c[0] == 'r' || c[0] == 'R') {
        if (sqm.mpsas < 0.) { //not an expected condition
          response = "r,";
        } 
        else if (sqm.mpsas < 10.) {
          response = "r, 0"; //space for no negative plus a zero for the 10's place
        }        
        else  {
          response = "r, ";
        }
        if (temp < 10.) {
          temp_string = ","; 
        }
        else if(temp < 0.) {
          temp_string = ",-0";
          temp = abs(temp);
        }       
        else {
          temp_string = ", 0"; //need 0 for padding -- logic breaks down at 100C
        }
      temp_string = String(temp_string + String(temp, 1) + "C");
      response = String(response + String(sqm.mpsas, 2) +
                 "m,0000005915Hz,0000000000c,0000000.000s" + temp_string);
      new_data = true;
    }
    }
    if (new_data) {
      Serial.println(response);
      new_data = false;
    }
  }

  merajTlac=digitalRead(2);
  if (merajTlac==1){
    meraj=true;
    delay(500);
    merajTlac=digitalRead(2);
    while (merajTlac==1){  //cakaj na uvolnenie tlacitka
      delay(100); 
      merajTlac=digitalRead(2);
    }
  }

  if (meraj){
    display.clearDisplay();
    display.setTextColor(WHITE);
    display.setTextSize(2);
    display.setCursor(0,30);  
    display.print(F("Wait..."));
    display.display();
    sqm.takeReading();
    //temp=get_temperature();    
    delay(100);
    start=millis();
    show=true;
    meraj=false;
  }
  
  if (show) {
    display.clearDisplay();
    display.setTextColor(WHITE);
    display.setTextSize(2);
    display.setCursor(0,0);  
    display.print(F("MPSAS"));
    display.setCursor(65,0);  
    display.print(sqm.mpsas);
    display.setCursor(0,32);  
    display.print(F("NELM"));
    display.setCursor(65,32);
    display.print(sqm.nelm);
    display.display();
    //Serial.print(millis() - start);  
    if ((millis() - start) >= 60000) { //1minuta = 60 000 -> zhasnutie displaya
      show=false; 
      //Serial.println("XX"); 
      } 
  }
  else {
    display.clearDisplay();
    display.display();
  }
  delay(100); 
}
