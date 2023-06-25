from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, ObjectProperty
from kivy.clock import Clock
from jnius import autoclass
from audiostream import get_input
import wave
#
import os
from android.permissions import request_permissions,Permission,check_permission
from kivy_garden.graph import Graph, LinePlot
import numpy as np 
from array import array
from datetime import datetime
 
#import tensorflow as tf
import zipfile
import wave, struct
import audioop

try:
  # Import TFLite interpreter from tflite_runtime package if it's available.
  from tflite_runtime.interpreter import Interpreter
  from tflite_runtime.interpreter import load_delegate
except ImportError:
  # If not, fallback to use the TFLite interpreter from the full TF package.
  import tensorflow as tf
  Interpreter = tf.lite.Interpreter
  load_delegate = tf.lite.experimental.load_delegate

 
 
#if not os.path.isdir("/sdcard/kivyrecords/"):
#    os.mkdir("/sdcard/kivyrecords/")

PATH = "rec_test1.wav"
 
recordtime = 5
samples_per_second = 60
 
 
class RootScreen(BoxLayout): #
    pass
 


       

class Recorder(object):
    def __init__(self):
        # get the needed Java classes
        self.MediaRecorder = autoclass('android.media.MediaRecorder')
        self.AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
        self.AudioFormat = autoclass('android.media.AudioFormat')
        self.AudioRecord = autoclass('android.media.AudioRecord')
    # define our system
        self.SampleRate = 44100
        #self.SampleRate = 16000
        self.ChannelConfig = self.AudioFormat.CHANNEL_IN_MONO
        self.AudioEncoding = self.AudioFormat.ENCODING_PCM_16BIT
        self.BufferSize = self.AudioRecord.getMinBufferSize(self.SampleRate, self.ChannelConfig, self.AudioEncoding)
        #self.outstream = self.FileOutputStream(PATH)
        self.sData = []
        #self.mic = get_input(callback=self.mic_callback, source='mic', buffersize=self.BufferSize)
        self.mic = get_input(callback=self.mic_callback, source='default', buffersize=self.BufferSize)
        print("This is the audio source")
        print(self.AudioSource)
        print("This is the mic channels")
        print(self.mic.channels)
        
        
        
        ###################################################
        # Step 1 - Load bird model
        ######################################################

        # Load TFLite model and allocate tensors.
        #This is to load the default yamnet model which you dont need to do
        #with open('lite-model_yamnet_tflite_1.tflite', 'rb') as fid:

        #Open the bird model
        with open('my_birds_model.tflite', 'rb') as fid:
            tflite_model = fid.read()    

        #interpreter = tf.lite.Interpreter('lite-model_yamnet_tflite_1.tflite')
        #interpreter = tf.lite.Interpreter(model_content=tflite_model)             
        self.interpreter = Interpreter(model_content=tflite_model) 
        
        
        ###################################################
        # Step 2 - Get labels/bird names from metadata inside mdel
        ######################################################

        try:
            #with zipfile.ZipFile('my_birds_model.tflite') as model_with_metadata:
            #with zipfile.ZipFile('./birds_models/my_birds_model.tflite') as model_with_metadata: 
            with zipfile.ZipFile('my_birds_model.tflite') as model_with_metadata: 
  
                if not model_with_metadata.namelist():
                    raise ValueError('Invalid TFLite model: no label file found.')


                #the file name below retrieves the default Yamnet model metadata
                #file_name = model_with_metadata.namelist()[0]
                #or
                #the file name below retrieves the new bird model metadata namely [1]
                file_name = model_with_metadata.namelist()[1]

                with model_with_metadata.open(file_name) as label_file:
                    label_list = label_file.read().splitlines()
                    print("label_list")
                    print(label_list)
                    #_label_list = [label.decode('ascii') for label in label_list]
                    self._label_list = [label.decode('utf-8') for label in label_list]
      
                    print("_label_list")
                    print(self._label_list)  #Should print list of bird codes ['azaspi1', 'chcant2', 'houspa', 'redcro', 'wbwwre1']
      
                    print(len(self._label_list))  # should print 5   
      
                    #print(test_data.index_to_label[0])
      
        except zipfile.BadZipFile:
            print('ERROR: Please use models trained with Model Maker or downloaded from TensorFlow Hub.')
            raise ValueError('Invalid TFLite model: no metadata found.')        
        
      
        
        
        
 
    def mic_callback(self, buf):
        self.sData.append(buf)
        print ('got : ' + str(len(buf)))
        print(self.sData)
        
        # convert our byte buffer into signed short array
        values = array("h", buf)

        # get right values only
        r_values = values[1::2]

        # reduce by 20%
        r_values = map(lambda x: x * 0.8, r_values)
        print("r_values")
        print(r_values)
        '''
        # you can assign only array for slice, not list
        # so we need to convert back list to array
        values[1::2] = array("h", r_values)
        print("values")
        print(values)
        '''
        # convert back the array to a byte buffer for speaker
        #sample.write(values.tostring())
 
 
    def start(self):
        self.mic.start()
        Clock.schedule_interval(self.readbuffer, 1/samples_per_second)
 
    def readbuffer(self, dt):
        self.mic.poll()
 
    def dummy(self, dt):
        print ("dummy")
 
    def stop(self):
        Clock.schedule_once(self.dummy, 0.5)
        Clock.unschedule(self.readbuffer)
        self.mic.stop()
        wf = wave.open(PATH, 'wb')
        wf.setnchannels(self.mic.channels)
        wf.setsampwidth(2)
        wf.setframerate(self.mic.rate)
        wf.writeframes(b''.join(self.sData))
        print("we at stop")
        wf.close()
        
        print("files in pwd")
        print(os.listdir())
        
        print("contents of sData")
        print(self.sData)
        
        print("finished creating wav file")     
        self.play()
        
        
    def play(self):
        MediaPlayer = autoclass('android.media.MediaPlayer')
        AudioManager = autoclass('android.media.AudioManager')

        self.sound = MediaPlayer()
        #self.sound.setDataSource(yourDataSource) #you can provide any data source, if its on the devie then the file path, or its url if you are playing online
        #self.sound.setDataSource('testaudio.mp4') 
        #self.audio_path = self.storage_path + "/wav/output2.wav"
        #self.audio_path = self.storage_path + "/wav/output1.wav" ##cant find folder
     
        
        
        
        #self.audio_path = dirCheck1 + "/wav/output1.wav"
        #self.audio_path = "/storage/emulated/0/org.example.c4k_tflite_audio1/wav/output1.wav"##Not found
        #self.audio_path = "/data/data/org.example.c4k_tflite_audio1/files/app/wav/output2.wav"
        #self.audio_path = "/data/data/org.example.c4k_tflite_audio1/files/app/output2.wav"        
        #self.audio_path  = "/data/data/org.example.c4k_tflite_audio1/files/app/testaudio.mp4"
        self.audio_path  = "rec_test1.wav"
     
        self.sound.setDataSource(self.audio_path) 
        self.sound.prepare()
        self.sound.setLooping(False) #you can set it to true if you want to loop
        self.sound.start()
        print("start play")

        e = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
       
        print("time of start playing audio")
        print(e)
        # You can also use the following according to your needs
        #self.sound.pause()
        #self.sound.stop()
        #self.sound.release()
        #self.sound.getCurrentPosition()
        #self.sound.getDuration()   
        
        #self.downsample()
        
    '''
    def downsample(self):
        with open("rec_test1.wav", 'wb') as of:
            of.write(message['audio'])
            audioFile = wave.open("audioData_original.wav", 'r')
            n_frames = audioFile.getnframes()
            audioData = audioFile.readframes(n_frames)
            originalRate = audioFile.getframerate()
            af = wave.open('audioData.wav', 'w')
            af.setnchannels(1)
            af.setparams((1, 2, 16000, 0, 'NONE', 'Uncompressed'))
            converted = audioop.ratecv(audioData, 2, 1, originalRate, 16000, None)
            af.writeframes(converted[0])
            af.close()
            audioFile.close()
    '''

 
 
    def model_inputs(self):
      
        ###################################################
        # Step 3 - Ensure the audio sample fits the model input
        ######################################################

        self.input_details = self.interpreter.get_input_details()
        print("input_details")
        print(input_details)
        self.waveform_input_index = self.input_details[0]['index']
        self.output_details = self.interpreter.get_output_details()
        print("output_details")
        print(self.output_details)

        #Dont need this it is for the default Yamnet model
        self.scores_output_index = self.output_details[0]['index']
        print("scores_output_index 0")
        print(self.scores_output_index)

        #Get the output scores of the bird model
        self.scores_output_index1 = self.output_details[1]['index']
        print("")
        print(self.scores_output_index1)

        #The below is to create a wavfile of silence for testing only
        #Input: 0.975 seconds of silence as mono 16 kHz waveform samples.
        #waveform = np.zeros(int(round(0.975 * 16000)), dtype=np.float32)
           
 
REC = Recorder()
'''
class RecordApp(App):
	
    def __init__(self, **kwargs):
        super(RecordApp, self).__init__(**kwargs)
        
        	
 
    def build(self):
        #request_permissions([Permission.INTERNET, Permission.RECORD_AUDIO,Permission.READ_EXTERNAL_STORAGE,Permission.WRITE_EXTERNAL_STORAGE])
        self.title = 'Recording Application'
        return RecordForm()
        #return Builder.load_file("look.kv")
  
'''     
        
class RecordForm(BoxLayout): #
    #b_record = ObjectProperty()
    #p_bar = ObjectProperty()
 
    def start_record(self):
        #self.b_record.disabled = True
        #self.p_bar.max = recordtime
        #REC.prepare()
        REC.start()
        Clock.schedule_once(self.stop_record, recordtime)
        #Clock.schedule_interval(self.update_display, 1/30.)
 
    def stop_record(self, dt):
        #Clock.unschedule(self.update_display)
        #self.p_bar.value = 0
        REC.stop()
        #self.b_record.disabled = False
 
    def update_display(self,dt):
        #self.p_bar.value = self.p_bar.value + dt
        print("here")        
        
'''
class JKMain(AnchorLayout):
    def __init__(self, **kwargs):
        super(JKMain, self).__init__(**kwargs)

    def change_text(self, layers):
        self.the_time.text = "Total Layers : " + str(layers)
        print("Total Layers = " + str(layers))

    def popup_func(self):

        content = ConfirmPopup()
        content.bind(on_answer=self._on_answer)
        self.popup = Popup(title="Select .zip file",
                           content=content,
                           size_hint=(None, None),
                           size=(500, 500),
                           auto_dismiss=False)
        self.popup.open()

    def _on_answer(self, instance, answer, obj):
        self.popup.dismiss()
'''

class Main(App):

    def build(self):
        #return JKMain()
        request_permissions([Permission.INTERNET, Permission.RECORD_AUDIO,Permission.READ_EXTERNAL_STORAGE,Permission.WRITE_EXTERNAL_STORAGE])
        return RecordForm()
        


if __name__ == "__main__":
    Main().run()


