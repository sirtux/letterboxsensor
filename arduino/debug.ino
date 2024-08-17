#include <Arduino.h>
#include "config.h"
#include "pins.h"
#include "lorawan.h"

void setup() {

  // set up serial line
  Serial.begin(115200);
  delay(1000);
  Serial.println("-------------------------");
  Serial.println("DEBUGGER");
  

  // set pinmodes
  pinMode(statusled, OUTPUT);
  pinMode(irled1, OUTPUT);
  pinMode(irled2, OUTPUT);
  pinMode(irdiode1, OUTPUT);
  pinMode(irdiode2, OUTPUT);
  pinMode(irsens1, INPUT);
  pinMode(irsens2, INPUT);

  // ADC mode
  //udrv_adc_set_mode(UDRV_ADC_MODE_3_3);

  // blink led once on startup
  digitalWrite(statusled,HIGH);
  delay(1000);
  digitalWrite(statusled,LOW);


// read sensor values and send lorawan package
void sensor_handler(void *) {

  // variables

  unsigned int s2 = 0; // sensor#2

  

  // measure sensor #2
  digitalWrite(irled2,HIGH);
  digitalWrite(irdiode2,HIGH);
  delay(10);
  for(int i = 0 ; i <3 ; i++){
    delay(250);
    s2 += analogRead(irsens2);
  }
  s2=s2/3;
  digitalWrite(irled2,LOW);
  digitalWrite(irdiode2,LOW);
  Serial.printf("Sensor#2: %d\r\n", s2);  

  Serial.println("-------------------------");


}


void loop(){
  // destroy this busy loop and use a timer instead,
  // so that the system thread can auto enter low power mode by api.system.lpm.set(1)
  sensorHandler()
  delay(1000)
}

