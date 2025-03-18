#include <AccelStepper.h>
#include <MultiStepper.h>
#include <Servo.h>
#include <LinkedList.h>


struct Move {
  float motorOneSteps;
  float motorTwoSteps;
  int magnetState;

  Move (float MotorOneSteps, float MotorTwoSteps, int MagnetState) {
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

const int speed = 1000;
const int homingSpeed = 400;

const int enPin = 8;

AccelStepper motor1(AccelStepper::DRIVER, motor1StepPin, motor1DirPin);
AccelStepper motor2(AccelStepper::DRIVER, motor2StepPin, motor2DirPin);

MultiStepper steppers;

// Limit Switches
const int limitSwitch1Pin = 9;
const int limitSwitch2Pin = 10;
int limitSwitch1State = 0;
int limitSwitch2State = 0;

//Servo motor variables
Servo myservo;

//Managing input Queue
LinkedList<Move*> moves;
int lastState = 0;

void setup() {
  // Begin Serial Connection
  Serial.begin(9600);

  // Stepper Motors
  motor1.setMaxSpeed(speed);
  motor2.setMaxSpeed(speed);
  motor1.setSpeed(speed);
  motor2.setSpeed(speed);
  
  pinMode(enPin,OUTPUT);
  digitalWrite(enPin,LOW);

  steppers.addStepper(motor1);
  steppers.addStepper(motor2);

  // Servo Motor
  myservo.attach(11);

  // Limit Switches
  pinMode(limitSwitch1Pin, INPUT_PULLUP);
  pinMode(limitSwitch2Pin, INPUT_PULLUP);
}

void loop() {
  ManageInputs();
  if (moves.size() > 0) {
    MoveGantry(moves.remove(0));
  }
}

void ManageInputs() {
  if (Serial.available() > 0) {
    float num1 = Serial.parseFloat();
    float num2 = Serial.parseFloat();
    int num3 = Serial.parseInt();
    Serial.read();
    
    Move* nextMove = new Move(num1, -num2, num3);
    moves.add(nextMove);
  }
}

void MoveGantry(Move* move) {
  // Magnet State instruction
  if (move->magnetState != lastState) {
    switch (move->magnetState) {
      case 0: 
        myservo.write(90);
        delay(200);
        break;
      case 1:
        myservo.write(270);
        delay(200);
        break;
      case -1:
        Zero();
        return;
    }
    lastState = move->magnetState;
  }
  
  int32_t positions[2];
  positions[0] = move->motorOneSteps + motor1.currentPosition();
  positions[1] = move->motorTwoSteps + motor2.currentPosition();

  steppers.moveTo(positions);
  while (steppers.run()){
    limitSwitch1State = digitalRead(limitSwitch1Pin); 
    limitSwitch2State = digitalRead(limitSwitch2Pin);
    if (limitSwitch1State == LOW){
      Serial.println("X");
      if (move->motorOneSteps <= 0 && move->motorTwoSteps >= 0) {
        Serial.println("S");
      }
      else {
        Serial.println("N");
        positions[0] = motor1.currentPosition() - 100; 
        positions[1] = motor2.currentPosition() + 100;
        steppers.moveTo(positions); 
        steppers.runSpeedToPosition();
      }
      Zero();
      break;
    }
    if (limitSwitch2State == LOW) {
      Serial.println("Y");
      if (move->motorOneSteps <= 0 && move->motorTwoSteps <= 0) {
        Serial.println("W");
      }
      else {
        Serial.println("E");
        positions[0] = motor1.currentPosition() - 100; 
        positions[1] = motor2.currentPosition() - 100;
        steppers.moveTo(positions); 
        steppers.runSpeedToPosition();
      }
      Zero()
      break;
    }
  }
  positions[0] = motor1.currentPosition();
  positions[1] = motor2.currentPosition();
  steppers.moveTo(positions);
  Serial.println("Arrived");
}


void Zero() {
  motor1.setSpeed(homingSpeed); 
  motor2.setSpeed(homingSpeed); 
  motor1.setMaxSpeed(homingSpeed); 
  motor2.setMaxSpeed(homingSpeed); 
  int32_t positions[2]; 
  positions[0] = motor1.currentPosition() - 5; 
  positions[1] = motor2.currentPosition() - 5; 
  do { 
    steppers.moveTo(positions); 
    positions[0] = motor1.currentPosition() - 5; 
    positions[1] = motor2.currentPosition() - 5; 
    //Check Position 
    limitSwitch2State = digitalRead(limitSwitch2Pin); 
    if (limitSwitch2State == LOW) { 
      break; 
    } 
  } 
  while (steppers.run()); 
  positions[0] = motor1.currentPosition() - 5; 
  positions[1] = motor2.currentPosition() + 5; 
  do { 
    steppers.moveTo(positions); 
    positions[0] = motor1.currentPosition() - 5; 
    positions[1] = motor2.currentPosition() + 5; 
    //Check Position 
    limitSwitch1State = digitalRead(limitSwitch1Pin);  
    if (limitSwitch1State == LOW) { 
      positions[0] = motor1.currentPosition(); 
      positions[1] = motor2.currentPosition(); 
      steppers.moveTo(positions); 
      break; 
    } 
  } 
  while (steppers.run()); 
  motor1.setMaxSpeed(speed); 
  motor2.setMaxSpeed(speed); 
  motor1.setSpeed(speed); 
  motor2.setSpeed(speed); 
  positions[0] = motor1.currentPosition() + 390; 
  positions[1] = motor2.currentPosition(); 
  steppers.moveTo(positions); 
  steppers.runSpeedToPosition(); 
  positions[0] = motor1.currentPosition() + 210; 
  positions[1] = motor2.currentPosition() - 210; 
  steppers.moveTo(positions); 
  steppers.runSpeedToPosition(); 
  Serial.println("Arrived");
}