# Imports
import time, datetime, os, stat
import logging
import signal, sys
from firebase.firebase import FirebaseApplication, FirebaseAuthentication  # authentication & realtime database

###########################################
# LOCAL FUNCTIONS
 
# Convenience function to both log to file and print to console
def log(message, is_error):
    if is_error:
        logger.error(message)
    else:        
        logger.info(message)
    print(message)        

# Return the path to the folder
# And create it if it doesn't exist
# os.path methods used from https://docs.python.org/2/library/os.path.html
def get_folder(folder_name):
    # Get the full path of the current file (__file__ is module attribute)
    full_path = os.path.realpath(__file__)
    #print(full_path + "\n")
    # Split between directory and file (head and tail)
    directory, filename = os.path.split(full_path)
    #print("Dir: " + directory + "\nFile: " + filename + "\n")
    # Define folder path
    folder_path = directory + "/" + folder_name + "/"
    #print(folder_path + "\n")
    # Create it if it doesn't exist
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)
        log(folder_name + " folder created:\n" + folder_path, False)
    # Return the path to the folder
    return folder_path

# For programtically creating paths within the same folder
def get_current_dir():
    # Get the full path of the current file (__file__ is module attribute)
    full_path = os.path.realpath(__file__)
    # Split between directory and file (head and tail)
    directory, filename = os.path.split(full_path)
    return directory

# Get the socket values from Firebase
# if issueChanges = True, signals will be sent if value has changed
# if issueChanges = False, signals not sent if value has changed (used for initial syncing)
def get_fb_sockets(issueChanges):
    #log("Checking for socket changes...", False)
    # Get the socket dictionary from Firebase
    sockets = fbApp.get('/sockets', None)
    
    #log("Sockets: " + str(sockets), False)
    
    # Get socket values from dictionary
    fb_socket_1 = sockets.get("socket1")
    fb_socket_2 = sockets.get("socket2")
    fb_socket_3 = sockets.get("socket3")
    fb_socket_4 = sockets.get("socket4")
    fb_socket_5 = sockets.get("socket5")
    
    # And whether or not to force an update
    # 0 = don't
    # 1 = do
    fb_force_update = sockets.get("forceUpdate")
    
    # Update & Log if different to current
    updated = False
    global socket_1, socket_2, socket_3, socket_4, socket_5
    if fb_socket_1 != socket_1:
        log("Socket 1 update: " + str(fb_socket_1), False)
        socket_1 = fb_socket_1
        updated = True
        if issueChanges:
            sendSignal(SOCKET_1_ON) if socket_1 == 1 else sendSignal(SOCKET_1_OFF)
    if fb_socket_2 != socket_2:
        log("Socket 2 update: " + str(fb_socket_2), False)
        socket_2 = fb_socket_2   
        updated = True
        if issueChanges:
            sendSignal(SOCKET_2_ON) if socket_2 == 1 else sendSignal(SOCKET_2_OFF)
    if fb_socket_3 != socket_3:
        log("Socket 3 update: " + str(fb_socket_3), False)
        socket_3 = fb_socket_3    
        updated = True
        if issueChanges:
            sendSignal(SOCKET_3_ON) if socket_3 == 1 else sendSignal(SOCKET_3_OFF)
    if fb_socket_4 != socket_4:
        log("Socket 4 update: " + str(fb_socket_4), False)
        socket_4 = fb_socket_4    
        updated = True 
        if issueChanges:
            sendSignal(SOCKET_4_ON) if socket_4 == 1 else sendSignal(SOCKET_4_OFF)
    if fb_socket_5 != socket_5:
        log("Socket 5 update: " + str(fb_socket_5), False)
        socket_5 = fb_socket_5   
        updated = True
        if issueChanges:
            sendSignal(SOCKET_5_ON) if socket_5 == 1 else sendSignal(SOCKET_5_OFF)
    
    if fb_force_update == 1:
        log("Forcing socket sync!", False)
        # Sync all sockets to current status
        syncSockets()
        # Reset the forceUpdate value on firebase so we don't do it again next loop
        resetForceUpdate()
        updated = True
    
    if updated:
        # TODO: visibly indicate update somehow
        log("TODO: visual indication of socket change", False)

# Sync the sockets with whatever status we currently have
def syncSockets():
    log("Syncing sockets...", False)
    log(str([socket_1, socket_2, socket_3, socket_4, socket_5]), False)
    sendSignal(SOCKET_1_ON) if socket_1 == 1 else sendSignal(SOCKET_1_OFF)
    sendSignal(SOCKET_2_ON) if socket_2 == 1 else sendSignal(SOCKET_2_OFF)
    sendSignal(SOCKET_3_ON) if socket_3 == 1 else sendSignal(SOCKET_3_OFF)
    sendSignal(SOCKET_4_ON) if socket_4 == 1 else sendSignal(SOCKET_4_OFF)
    sendSignal(SOCKET_5_ON) if socket_5 == 1 else sendSignal(SOCKET_5_OFF)
    
# Send 433MHz signal code
def sendSignal(code):
    log("TODO: send signal " + str(code), False)
    
# Reset force update
def resetForceUpdate():
    # Reset Firebase's value to 0
    result = fbApp.put('/sockets', 'forceUpdate', 0)    
    # Log
    log("Resetting Firebase's forceUpdate to 0.", False)
    # Return the result in case we want to check it
    return result
          
# Cleanup
def cleanup():
    log("Cleaning up and terminating...", False)
    # Archive the log
    os.rename(log_file_path, archiveFolder + "/" + time.strftime("%Y-%m-%d:%H-%M-%S") + " " + log_file_name)

# Graceful signal interupt
def interupt_signal_handler(signal, frame):
    log("Signal detected: " + str(signal), False)
    # Call the cleanup
    cleanup()
    sys.exit(0)
  
# END LOCAL FUNCTIONS
###########################################

# Set up logger
logger = logging.getLogger("HomeAutomation")
log_file_name = "HomeAutomation.log"
log_file_path = get_current_dir() + "/" + log_file_name
logger_handler = logging.FileHandler(log_file_path)
logger_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
logger_handler.setFormatter(logger_formatter)
logger.addHandler(logger_handler)
logger.setLevel(logging.INFO)

log("Starting up...", False)

# Register the signal interupt handlers
log("Registering signal interupt handlers...", False)
for sig in [signal.SIGTERM, signal.SIGINT]:
    signal.signal(sig, interupt_signal_handler)        

# Variable/Object definition before entering loop

# Socket statuses (1 = on, 0 = off)
# (defaults before firebase queried)
socket_1 = 1
socket_2 = 1
socket_3 = 1
socket_4 = 1
socket_5 = 1

# RF codes for sockets
SOCKET_1_ON = 4308444
SOCKET_1_OFF = 4308436
SOCKET_2_ON = 4308442
SOCKET_2_OFF = 4308434
SOCKET_3_ON = 4308441
SOCKET_3_OFF = 4308433
SOCKET_4_ON = 4308445
SOCKET_4_OFF = 4308437
SOCKET_5_ON = 4308443
SOCKET_5_OFF = 4308435

# Firebase App
log("Initialising Firebase...", False)
fbApp = FirebaseApplication('https://home-automation-project-fa23c.firebaseio.com/', authentication=None) 

# Firebase Authentication
authentication = FirebaseAuthentication('08hbOtRkv9btYK6obDR43b34rl2yx6BpVs4rgoEN', 'rseamanrpi@gmail.com')
fbApp.authentication = authentication

# Firebase socket values
get_fb_sockets(False)

# Local Folders
archiveFolderName = "Archive"  # vairable used to ensure same name used below
archiveFolder = get_folder(archiveFolderName)

# Times to wait
main_loop_delay = 1
time_between_check_fb_sockets = 1  # delay between checking for socket changes on Firebase

# Last done times 
# Defined after fetching FB values
last_check_sockets = int(time.time()) # already synced initially above, no need to allow immediately

# Main Loop
while True:
    
    try:
        # Get the current day / time        
        curr_time_sec=int(time.time())
        curr_time = time.strftime("%Y-%m-%d:%H-%M-%S")
        
        # Check for socket changes
        if curr_time_sec - last_check_sockets > time_between_check_fb_sockets:
            get_fb_sockets(True)
            last_check_sockets = curr_time_sec
         
        #Slow down the loop
        time.sleep(main_loop_delay)
        
    except KeyboardInterrupt:
        log("Keyboard Interrupt detected, stopping loop...", False)
        break
    
# Cleanup
cleanup()
