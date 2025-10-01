// Controller for 16 sensors
const int multiplexorOne = A0;
const int multiplexorOnePins[4] = {10, 11, 12, 13};

// Internal Variables
int thresholdValue = 550;
int numberOfSensors = 5;
bool *sensorStates;

int readSensor(int pinNumber, int multiplexer) {
  for (int i = 0; i < 4; i++) {
    digitalWrite(multiplexorOnePins[i], (pinNumber >> i) & 1);
  }
  return analogRead(multiplexer);
}

void updateSensorStates() {
  uint64_t board_state = 0;
  for (int i = 0; i < numberOfSensors; i++) {
    int sensorValue = readSensor(i, multiplexorOne);
    board_state |= (uint64_t)(sensorValue > thresholdValue) << i;
  }

  Serial.println((unsigned long long)board_state);
}

void setup() {
  sensorStates = new bool[numberOfSensors];
  for (int i = 0; i < 4; i++) {
    pinMode(multiplexorOnePins[i], OUTPUT);
  }
  pinMode(multiplexorOne, INPUT);
  Serial.begin(9600);
}

void loop() {
  updateSensorStates();
}


