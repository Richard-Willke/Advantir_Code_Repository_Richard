from statemachine import StateMachine, State
#import Machine_Pipe_Sketch

class SwirlGoStateMachineModel(StateMachine):
    #initialization  = State('Initialization', initial = True)
    #createPipes     = State('CreatePipes')
    #setupGPIOs      = State('setupGPIOs')
    #initializeESP32 = State('initializeESP32')

    insertScreen            = State('InsertScreen', initial = True)
    identifyScreen          = State('identifyScreen')
    recognizedPodScreen     = State('recognizedPodScreen')
    blendingPodScreen       = State('blendingPodScreen')
    readyToDispenseScreen   = State('readyToDispenseScreen')
    dispensingPodScreen     = State('dispensingPodScreen')
    extraDispensingScreen   = State('extraDispensingScreen')
    removePodScreen         = State('removePodScreen')

    #loadingScreen   = State('loadingScreen')
    #loopingMain     = State('looping')
    #openCapScreen   = State('openCapScreen')
    #thankYouScreen  = State('thankYouScreen')

    '''
    screenControll
    showFrame
    UI2MA_pipe_write
    jsonOrganizeLoad
    checkInternetConnection
    checkVersionFile
    sampleApp
    '''

    inserted                = insertScreen.to(identifyScreen)
    identified              = identifyScreen.to(recognizedPodScreen)
    not_identified          = identifyScreen.to(insertScreen)
    recognized              = recognizedPodScreen.to(blendingPodScreen)
    not_recognized          = recognizedPodScreen.to(insertScreen)
    blended                 = blendingPodScreen.to(readyToDispenseScreen)
    dispense_ready          = readyToDispenseScreen.to(dispensingPodScreen)
    dispensed               = dispensingPodScreen.to(extraDispensingScreen)
    extra_dispense          = extraDispensingScreen.to(extraDispensingScreen)
    finished_dispensing     = extraDispensingScreen.to(removePodScreen)
    removed_pod             = removePodScreen.to(insertScreen)

    '''
    on_inserted()
    on_identified()
    on_not_identified()
    on_recognized()
    on_not_recognized()
    on_blended()
    on_dispense_ready()
    on_dispensed()
    on_extra_dispense()
    on_finished_dispensing()
    on_removed_pod()
    '''
    def on_inserted(self):
        print("capsule inserted")

    def on_identified(self):
        print("identified capsule")

    def on_not_identified(self):
        print("no capsule identified")

    def on_recognized(self):
        print("flavour recognized")

    def on_not_recognized(self):
        print("flavour not recognized")

    def on_blended(self):
        print("blending complete")

    def on_dispense_ready(self):
        print("ready to dispense")

    def on_dispensed(self):
        print("dispensed capsule contigents")

    def on_extra_dispense(self):
        print("extra dispense complete")

    def on_finished_dispensing(self):
        print("finished dispensing, removing pod")

    def on_removed_pod(self):
        print("pod removed, going back to start")




SwirlGOMachine = SwirlGoStateMachineModel()
SwirlGOMachine.inserted()
