#include <VarSpeedServo.h>
#include <LiquidCrystal.h>
#include <string.h>
#include <stdlib.h>


//LCD SETUP
const uint8_t rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

const uint8_t lcd_data_precision = 5;
const uint8_t data_len = 64;


//SERVO SETUP
const uint8_t min_sweep_angle = 0;
const uint8_t max_sweep_angle = 180;
uint8_t low = min_sweep_angle;
int angle = low; 
int og_angle = angle; 
uint8_t high = max_sweep_angle;
int decay_rate = 3;
int sample_step = 5;
int sample_delay = 100;

VarSpeedServo servo;
const uint8_t servo_pin = 9;


//DATA COLLECTION SETUP
int f, s11, s21;
char data[data_len];
boolean new_data = false;

//boolean running1 = true; 


void setup() {
  Serial.begin(115200);
  
  lcd.begin(16, 2);
  lcd.setCursor(0, 0);
  lcd.print("Init...");

 servo.attach(servo_pin); //attaches servo motor to i/o pin 9 
}


void loop() {

  //int angle = low; 
  int max_angle = 0;
  int final_angle = 0;
  int s21 = 0; 
  int max_s21 = 0; 
  int final_s21 = 0;  

  
    while (angle <= (og_angle + 180) ) { //while the minimum angle  is less than itself plus 180
      servo.write(angle, 10); //want to read vna (s21) data at each angle 
      read_vna_data(); 
      
      if (new_data) {
        if (s21 > max_s21) {
          if (angle == 0 || angle == 5 || angle == 10) {
            max_s21 = 0; 
            max_angle = 0; 
          } 
          else {
            max_s21 = s21;
            max_angle = angle; }
        }
        //prints new data to LCD
          s21 = atoi(data); //converts string to an integer
          lcd.clear();
          lcd.setCursor(0, 0); //
          lcd.print("    S21: ");
          lcd.print(s21);
          lcd.setCursor(0, 1);
          lcd.print("Max S21: ");
          lcd.print(max_s21);
          
          new_data = false;
  
          angle += sample_step; //now we want to increment the angle 
    
          delay(sample_delay); //delay for a small period of time
      }
    }

 final_s21 = max_s21; 
 final_angle = max_angle; 

 //lcd prints final angle and max s21 
 lcd.clear();
 lcd.setCursor(0, 0); //
 lcd.print("Max S21: ");
 lcd.print(final_s21); 
 lcd.setCursor(0,1); 
 lcd.print("Final Angle:  "); 
 lcd.print(final_angle); 

//servo moves to max angle position
 servo.write(final_angle, 10); 
 delay(10000);

 //RESET SEQUENCE
 max_s21 = 0; 
 og_angle = max_angle; 
 angle = max_angle; 
 lcd.clear();
 lcd.setCursor(0, 0); //
 lcd.print(" S21 Reset: ");
 lcd.print(max_s21);
 //servo.write(0, 30); 
 delay(7000);
 
}

//helper function to read vna data
void read_vna_data() {
    static byte ndx = 0;
    char end_marker = ';';
    char rc;
    
    while (Serial.available() > 0 && !new_data) {
        rc = Serial.read();

        if (rc != end_marker) {
            data[ndx] = rc;
            ndx++;
            if (ndx >= data_len) {
                ndx = data_len - 1;
            }
        } else {
            data[ndx] = '\0';
            ndx = 0;
            
            new_data = true;
        }
    }

} 
