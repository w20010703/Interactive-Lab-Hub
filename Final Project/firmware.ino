// ============================================================
//  SMART COCKTAIL MACHINE – ARDUINO FIRMWARE
//  Controls 6 peristaltic pumps via relay board
//  Commands from Raspberry Pi (USB serial):
//
//  RUN <pump> <ms>           -> run pump for <ms> milliseconds
//  DOSE <pump> <ml>          -> run pump long enough for <ml> mL
//  ON <pump>                 -> manual ON
//  OFF <pump>                -> manual OFF
//
//  Pump index range: 0–5
//  Pins used: 2,3,4,5,6,7 (connected to IN1–IN6 on relay board)
// ============================================================

const int pumpPins[6] = {2, 3, 4, 5, 6, 7};

// Estimated flow rate in mL/sec per pump.
// IMPORTANT: Replace with real calibrated values later!
float mlPerSec[6] = {
  2.5,   // Pump 0
  2.5,   // Pump 1
  2.5,   // Pump 2
  2.5,   // Pump 3
  2.5,   // Pump 4
  2.5    // Pump 5
};


// ------------------------------------------------------------
// Setup
// ------------------------------------------------------------
void setup() {
  Serial.begin(9600);

  // Initialize all pump pins
  for (int i = 0; i < 6; i++) {
    pinMode(pumpPins[i], OUTPUT);
    digitalWrite(pumpPins[i], LOW);
  }

  Serial.println("ARDUINO READY");
  Serial.println("Commands:");
  Serial.println("  RUN <pump> <ms>");
  Serial.println("  DOSE <pump> <ml>");
  Serial.println("  ON <pump>");
  Serial.println("  OFF <pump>");
}


// ------------------------------------------------------------
// Main Loop
// ------------------------------------------------------------
void loop() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd.startsWith("RUN")) {
    handleRUN(cmd);
  }
  else if (cmd.startsWith("DOSE")) {
    handleDOSE(cmd);
  }
  else if (cmd.startsWith("ON")) {
    handleON(cmd);
  }
  else if (cmd.startsWith("OFF")) {
    handleOFF(cmd);
  }
}


// ------------------------------------------------------------
// RUN <pump> <ms>
// Direct time-based control
// ------------------------------------------------------------
void handleRUN(const String &cmd) {
  int s1 = cmd.indexOf(' ');
  int s2 = cmd.indexOf(' ', s1 + 1);

  if (s1 < 0 || s2 < 0) {
    Serial.println("ERR FORMAT: USE 'RUN <pump> <ms>'");
    return;
  }

  int pump = cmd.substring(s1 + 1, s2).toInt();
  int ms   = cmd.substring(s2 + 1).toInt();

  if (!validPump(pump)) return;

  Serial.print("RUN PUMP ");
  Serial.print(pump);
  Serial.print(" FOR ");
  Serial.print(ms);
  Serial.println(" ms");

  digitalWrite(pumpPins[pump], HIGH);
  delay(ms);
  digitalWrite(pumpPins[pump], LOW);

  Serial.println("DONE");
}


// ------------------------------------------------------------
// DOSE <pump> <ml>
// Volume-based dosing using mlPerSec calibration
// ------------------------------------------------------------
void handleDOSE(const String &cmd) {
  int s1 = cmd.indexOf(' ');
  int s2 = cmd.indexOf(' ', s1 + 1);
  
  if (s1 < 0 || s2 < 0) {
    Serial.println("ERR FORMAT: USE 'DOSE <pump> <ml>'");
    return;
  }

  int pump = cmd.substring(s1 + 1, s2).toInt();
  float ml = cmd.substring(s2 + 1).toFloat();

  if (!validPump(pump)) return;

  if (ml <= 0) {
    Serial.println("ERR: ml must be > 0");
    return;
  }

  float rate = mlPerSec[pump];
  if (rate <= 0) {
    Serial.println("ERR: flow rate not set for this pump");
    return;
  }

  float timeSec = ml / rate;
  unsigned long timeMs = (unsigned long)(timeSec * 1000);

  Serial.print("DOSE ");
  Serial.print(ml);
  Serial.print(" mL USING PUMP ");
  Serial.print(pump);
  Serial.print(" @ ");
  Serial.print(rate);
  Serial.print(" mL/s  -> ");
  Serial.print(timeMs);
  Serial.println(" ms");

  digitalWrite(pumpPins[pump], HIGH);
  delay(timeMs);
  digitalWrite(pumpPins[pump], LOW);

  Serial.println("DONE");
}


// ------------------------------------------------------------
// ON <pump>  (Manual ON)
// OFF <pump> (Manual OFF)
// ------------------------------------------------------------
void handleON(const String &cmd) {
  int space = cmd.indexOf(' ');
  int pump = cmd.substring(space + 1).toInt();

  if (!validPump(pump)) return;

  digitalWrite(pumpPins[pump], HIGH);
  Serial.print("PUMP ");
  Serial.print(pump);
  Serial.println(" ON");
}

void handleOFF(const String &cmd) {
  int space = cmd.indexOf(' ');
  int pump = cmd.substring(space + 1).toInt();

  if (!validPump(pump)) return;

  digitalWrite(pumpPins[pump], LOW);
  Serial.print("PUMP ");
  Serial.print(pump);
  Serial.println(" OFF");
}


// ------------------------------------------------------------
// Validation helper
// ------------------------------------------------------------
bool validPump(int pump) {
  if (pump < 0 || pump > 5) {
    Serial.println("ERR: pump index must be 0–5");
    return false;
  }
  return true;
}
