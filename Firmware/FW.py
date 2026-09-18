import time
import board
import analogio
import digitalio
from RDA5807 import RDA5807
#Pins

tune = analogio.AnalogIn(board.A0)
button = digitalio.DigitalInOut(board.D7)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

#Settings
FM_MIN = 87.5 #min freq
FM_MAX = 108.0 #max freq
VOLUME = 8 #Change later when testing
RETUNE_STEP = 0.1 #Only retune when it moves at least (retune step) MHz
DEBOUNCE = 0.05
STATUS_INTERVAL = 2.0 #Print status every (interval) seconds

#Radio init
radio = RDA5807(i2c=None, band=BAND_87_108, space=SPACE_200K)
radio.set_volume(0) #Start muted
radio.set_mono(True)#Reduce oise incase signal is weak


#State
radio_on = False
last_freq = None 
last_button_state = True
button_handled= False
last_debounce_time = time.monotonic()
last_status_time = time.monotonic()

def read_pot_freq(): #reads the frequency from the pot and turns to MHZ
    frac = tune.value / 65535
    return FM_MIN + frac * (FM_MAX - FM_MIN)

def print_status():
    status = radio.read_status()
    print(
        "Freq: {:.1f} MHZ / Stereo: {} / RSSI: {} / Station: {}".format(
            status["freq_mhz"],
            status["stereo"],
            status["rssi"],
            status["fm_true"]
        )
    )

def toggle_power():
    global radio_on
    radio_on = not radio_on
    radio.set_volume(VOLUME if radio_on else 0)
    print("Radio on" if radio_on else "Radio off")


def handle_button():
    global last_button_state, button_handled, last_debounce_time
    reading = button.value

    if reading != last_button_state:
        last_debounce_time = time.monotonic()

    if (time.monotonic() - last_debounce_time) > DEBOUNCE:
        if reading is False and not button_handled:
            toggle_power()
            button_handled = True
        elif reading is True:
            button_handled = False

    last_button_state = reading


#Inital values
start_freq = read_pot_freq() #we can check the frequency the potentiometer is at and start there
radio.tune(start_freq)
last_freq = start_freq
print_status()

#Main loop
while True:
    handle_button()
    if radio_on:
        freq = read_pot_freq()
        if abs(freq - last_freq) >= RETUNE_STEP:
            radio.tune(freq)
            last_freq = freq
            print_status()

        if (time.monotonic() - last_status_time) >= STATUS_INTERVAL:
         print_status()
         last_status_time = time.monotonic()


        time.sleep(0.1) #lil delay to avoid waiting


