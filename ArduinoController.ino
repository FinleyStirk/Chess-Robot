#include <AccelStepper.h>
#include <MultiStepper.h> 
#include <ezButton.h>
#include <Servo.h>
#include <LinkedList.h>
#include <MFRC522.h>
#include <SPI.h>

#define RST_PIN 9
#define SS_PIN 10

struct Move {
  float motorOneSteps;
  float motorTwoSteps;
  float magnetState;

  Move (float MotorOneSteps, float MotorTwoSteps, float MagnetState) {
    motorOneSteps = MotorOneSteps;
    motorTwoSteps = MotorTwoSteps;
    magnetState = MagnetState;
  }
};

//Stepper Motor variables
int motor1DirPin = 5;
int motor2DirPin = 6;

int motor1StepPin = 2;
int motor2StepPin = 3;

const int maxSpeed = 800;

const int enPin = 8;

AccelStepper motor1(AccelStepper::DRIVER, motor1StepPin, motor1DirPin);
AccelStepper motor2(AccelStepper::DRIVER, motor2StepPin, motor2DirPin);

MultiStepper steppers;

//Servo motor variables
Servo myservo;

//RFID Variables
MFRC522 mfr522(SS_PIN, RST_PIN);

//Managing input Queue
LinkedList<Move*> moves;
float lastState = 0;

void setup() {
  Serial.begin(9600);

  SPI.begin()
  mfrc522.PCD_Init();
  delay(4);
  mfrc522.PCD_DumpVersionToSerial()

  myservo.attach(11);

  motor1.setMaxSpeed(maxSpeed);
  motor2.setMaxSpeed(maxSpeed);

  steppers.addStepper(motor1);
  steppers.addStepper(motor2);

  pinMode(enPin,OUTPUT);
   
  digitalWrite(enPin,LOW);
}

void loop() {
  ManageInputs();
  if (moves.size() != 0) {
    MoveGantry(moves.remove(0));
  }
}

void ManageInputs() {
  
  if (Serial.available() > 0) {
    float num1 = Serial.parseFloat();
    float num2 = Serial.parseFloat();
    float num3 = Serial.parseFloat();
    Serial.read();
    
    Move* nextMove = new Move(num1, num2, num3);
    moves.add(nextMove);
  }
}

void MoveGantry(Move* move) {
  if (move->magnetState != lastState) {
    if (move->magnetState == 0) {
      myservo.write(90);
      delay(200);
    }
    if (move->magnetState == 1) {
      myservo.write(270);
      delay(200);
    }
    lastState = move->magnetState;
  }
  
  int32_t positions[2];
  positions[0] = move->motorOneSteps + motor1.currentPosition();
  positions[1] = move->motorTwoSteps + motor2.currentPosition();

  steppers.moveTo(positions);
  while (steppers.run()){
    ManageInputs();
  }
  Serial.println("Arrived");
}
