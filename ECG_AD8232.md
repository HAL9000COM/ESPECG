# ECG Configuration for SparkFun AD8232

## SparkFun AD8232 Module

AD8232 [Datasheet](<https://www.analog.com/media/en/technical-documentation/data-sheets/ad8232.pdf>)

SparkFun AD8232 Module [Docs](https://github.com/sparkfun/AD8232_Heart_Rate_Monitor)

Gain:100

OpAmp Gain:11

Total Gain:1100

Supply Voltage: 3.3V

Typical Vref: 1.5V

SparkFun REFIN: Vs/2, 1.65V

3 electrode:

- RA
  - Connected to pin 3, IN-. Instrumentation Amplifier Negative Input.

- LA
  - Connected to pin 2, IN+. Instrumentation Amplifier Positive Input.

- RL
  - Connected to pin 5, RLD. Right Leg Drive Output. For improving common mode rejection.

## Connections

- Lead I

    |Label|Placement|
    |-----|---------|
    |RA   |RA       |
    |LA   |LA       |
    |RL   |RL       |

- Lead II

    |Label|Placement|
    |-----|---------|
    |RA   |RA       |
    |LA   |LL       |
    |RL   |RL       |

- Lead III

    |Label|Placement|
    |-----|---------|
    |RA   |LA       |
    |LA   |LL       |
    |RL   |RL       |
