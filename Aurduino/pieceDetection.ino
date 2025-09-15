// Controller for 16 sensors
const int multiPlexerOne = A0;
const int multiPlexerOnePins[4] = {13, 12, 11, 10};

// Internal Variables
int thresholdValue = 550;
int numberOfSensors = 8;
bool *sensorStates;

int readSensor(int sensor, int multiplexer) {
  for (int i = 0; i < 4; i++) {
    Serial.print((sensor >> i) & 1);
    digitalWrite(multiPlexerOnePins[i], (sensor >> i) & 1);
  }
  return analogRead(multiplexer);
}

void updateSensorStates() {
  String transmittingData = "";
  for (int i = 0; i < numberOfSensors; i++) {
    int sensorValue = readSensor(i, multiPlexerOne);
    transmittingData += sensorValue > thresholdValue ? "1" : "0";
  }
  Serial.println();
}

void setup() {
  sensorStates = new bool[numberOfSensors];
  for (int i = 0; i < 4; i++) {
    pinMode(multiPlexerOnePins[i], OUTPUT);
  }
  pinMode(multiPlexerOne, INPUT);
  Serial.begin(9600);
}

void loop() {
  updateSensorStates();
}