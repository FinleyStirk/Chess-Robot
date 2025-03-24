// Controller for 16 sensors
const int multiPlexerOne = A0;

// Internal Variables
int thresholdValue = 550;
int numberOfSensors = 5;
bool *sensorStates;

String toBin(int num) {
  String binary = "";
  for (int i = 0; i < 4; i++) {
    binary = num % 2 + binary;
    num /= 2;
  }
  return binary;
}

int readSensor(int pinNumber, int multiplexer) {
  String binPinNumber = toBin(pinNumber);
  for (int i = 3; i >= 0; i--) {
    int pin = 13 - i;
    if (binPinNumber.charAt(i) == '1') {
      digitalWrite(pin, HIGH);
    }
    else {
      digitalWrite(pin, LOW);
    }
  }
  return analogRead(multiplexer);
}

void updateSensorStates() {
  String transmittingData = "";
  for (int i = 0; i < numberOfSensors; i++) {
    int sensorValue = readSensor(i, multiPlexerOne);
    transmittingData += sensorValue > thresholdValue ? "1" : "0";
  }
  Serial.println(transmittingData);
}

void setup() {
  sensorStates = new bool[numberOfSensors];
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);
  pinMode(12, OUTPUT);
  pinMode(13, OUTPUT);
  pinMode(multiPlexerOne, INPUT);
  Serial.begin(9600);
}

void loop() {
  updateSensorStates();
}