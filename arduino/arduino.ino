// PIN information
#define LIGHT_BLOCK_PIN 5
#define FAN_PIN 3

// Global variable
char prefix = ' ';
bool get_cmd = false;
int pwm = 0;

void setup()
{
    // Set baudrate
    Serial.begin(9600);

    // Setup pin mode
    pinMode(LIGHT_BLOCK_PIN, INPUT);
    pinMode(FAN_PIN, OUTPUT);

    // Default State
    analogWrite(FAN_PIN, 255-pwm);
}

void loop()
{
    int block_counter = 0;

    /* Process command */
    if (get_cmd) {

        /* Pull request from Pi */
        /* Return the current_rps value of the fan to the Pi */
        if (prefix == 'p') {

            /* Count the number of light block for a predefined period of time. */
            int block_prev = 0;
            int block_current = 0;
            unsigned long start_time = millis();
            for (int i = 0; i < 20000; i++) {
                block_current = digitalRead(LIGHT_BLOCK_PIN);
                if (block_current != block_prev) {
                    block_counter += 1;
                }
                block_prev = block_current;
            }
            unsigned long end_time = millis();

            /* Caculate current_rps */
            float elapsed_time = (end_time-start_time)/1000.0;
            int current_rps = (int)((block_counter/4)/elapsed_time);
            Serial.println(current_rps);

        } else if (prefix == 'r') {

            /* Update pwm to the responsed ideal_pwm from Pi */
            analogWrite(FAN_PIN, 255 - pwm);

        } else {
            ;
        }
        get_cmd = false;
    }
}

/*
 * If there is any content in the serial buffer, this function
 * will be called before loop()
 */
void serialEvent() {

    /* Command line buffer */
    int idx = 0;
    char buffer[256] = { '\0' };

    /* Reset command type */
    prefix = ' ';

    /* Read one byte a time until there is no content in serial buffer */
    while (Serial.available()) {
        if (prefix == 'r' || prefix == 'p') {
            buffer[idx] = (char)Serial.read();
            idx++;
        } else {
            prefix = (char)Serial.read();
        }

        /* This should be related to the baudrate of the serial communication */
        /* Sleep 0.001 second for next byte */
        delay(1);
    }

    /* Get ideal_pwm when the command is a response command from Pi */
    if (prefix == 'r') {
        buffer[idx] = '\0';
        pwm = atoi(buffer);
    }

    /* Notify Uno's main loop to respond to the request from Pi */
    get_cmd = true;
}
