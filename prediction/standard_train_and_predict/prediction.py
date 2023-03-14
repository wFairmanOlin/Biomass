import matplotlib.pyplot as plt
import numpy as np
import sys
import tensorflow as tf
from keras.models import Sequential
from keras.layers.core import Dense, Activation, Dropout, Flatten
from keras.layers import Convolution2D
from keras.layers.recurrent import LSTM, SimpleRNN, GRU
import keras as keras
from keras import backend as K
# from preprocessing_LOBO import preprocess_lobo  MUST WRITE YOUR OWN DATASET PREPROCESSING TO GET THE DATA FROM FILES
from phased_lstm_keras.PhasedLSTM import PhasedLSTM as PLSTM
np.random.seed(1234)
tf.random.set_seed(35345)

def normalize(data):
    # print('ds', data.shape)
    normalized = np.zeros(data.shape)
    for i in range(data.shape[1]):    
        dat = data[:, i]
        normalized[:, i] = (dat - dat.mean()) / dat.std()
    
    return normalized, data[:,0].mean(), data[:,0].std()


class lstm_model:
    
    def __init__(self):
        
        self.input_size = 7  # depth of the data (ex. DO, Temp, Wind speed = 3 )
        self.output_size = self.input_size  # 1 for 1 time-step prediction, input-size for longer look-ahead
        self.hidden_units = 50
        self.epochs = 300 #how many times you want to it to run through all the data and optimize (1 run through = 1 epoch)
        self.activation = 'tanh' #(-1, +1)
        #self.activation = 'relu' #if you want to use this instead of tanh, you must re-normalize the numebrs for (0,1)
        self.input_horizon = 24  #how many time steps back it looks at to make its prediction
        self.test_steps = 100 # set it wit regard to the dataset dimension (if there are 1000 time-steps set it to be like 200); how many time steps will be used for for practice predictions using data it already has (the number you set for this)
        self.lookahead = 2 #how many time steps in the future you want to predict; accuracy is the average of the next (x) timesteps
    
        self.x_train = None
        self.y_train = None
        self.x_test = None
        self.y_test = None
    
    def load_dataset(self, site_number):

        data = preprocess_lobo(site_number)
        #sys.exit()
        norm_data, self.mean, self.std = normalize(data)
        
        train_steps = data.shape[0] - self.input_horizon - self.test_steps 
        data_arranged = []
        for index in range(data.shape[0] - self.input_horizon):
            data_arranged.append(norm_data[index: index + self.input_horizon])
        data_arranged = np.array(data_arranged)
        self.x_train = data_arranged[:train_steps] # supposed to be traintepx x 12 x in_dim
        self.y_train = norm_data[self.input_horizon: train_steps + self.input_horizon, 0]
        
        self.x_test = data_arranged[train_steps:train_steps + self.test_steps - self.input_horizon]
        self.y_test = norm_data[train_steps + self.input_horizon:train_steps + self.test_steps, 0]
        print('Xtrain', self.x_train.shape)
        
    def build_lstm_layer(self):
        
        model = Sequential()        
        model.add(LSTM(return_sequences=False, input_shape=(self.input_horizon, self.input_size),
                       units=self.hidden_units)) # activation is tanh
        model.add(Dense(units=self.output_size))
        keras.layers.LeakyReLU(alpha=0.3)
        optimizer = keras.optimizers.Adadelta(learning_rate=0.003, rho=0.999, clipnorm=0.7) 
        model.compile(loss="mean_squared_error", optimizer=optimizer)
        #model.compile(loss=correntropy_loss, optimizer=optimizer)
        
        return model
    
    def build_plstm_layer(self):
        
        model = Sequential()
        model.add(PLSTM(input_shape=(self.input_horizon, self.input_size),
                      units=self.hidden_units)) # activation is tanh   
        model.add(Dense(units=self.output_size))
        optimizer = keras.optimizers.Adadelta(learning_rate=0.003, rho=0.999, clipnorm=0.7) # for long dataset
        model.compile(loss="mean_squared_error", optimizer=optimizer)
        #model.compile(loss=correntropy_loss, optimizer=optimizer)
        
        return model
        

    def run(self):
        global first
        global weights
        print (' Training LSTM  ...')
        print('xtrain', self.x_train.shape)
        print('ytrain', self.y_train.shape)
        lstmModel = self.build_plstm_layer()  
        #lstmModel = self.build_lstm_layer()  # uncomment and comment the line above to use LSTM rather than PLSTM
        
        callback = tf.keras.callbacks.LearningRateScheduler(scheduler) 
        # for short ds standard bs is 32, if the GPU allows set batch_size bigger (64, 128, 256...)
        lstmModel.fit(self.x_train, self.y_train, batch_size=64, epochs=self.epochs, callbacks=[callback] )  # try it also without the callback (scheduler)

        # testing
        print ('...... TESTING  ...')
        y_pred = np.zeros_like(self.y_test)
        for timestep in range(self.x_test.shape[0]):
            index = timestep % self.lookahead
            if index == 0:
                testInputRaw = self.x_test[timestep]
                testInputShape = testInputRaw.shape  # 12x10
                testInput = np.reshape(testInputRaw, [1, testInputShape[0], testInputShape[1]])
            else:
                testInputRaw = np.vstack((testInput, self.predicted[ind-1]))
                testInput = np.delete(testInputRaw, 0, axis=0)
                testInputShape = testInput.shape
                testInput = np.reshape(testInput, [1, testInputShape[0], testInputShape[1]])

            y_pred[timestep] = lstmModel.predict(testInput)

        y_pred_d = y_pred*self.std + self.mean
        y_test_d = self.y_test*self.std + self.mean
        
        rmse = np.sqrt((np.mean((np.absolute(y_pred_d - y_test_d)) ** 2)))
        accuracy = 1 - np.mean(np.abs(np.true_divide(y_test_d - y_pred_d, y_test_d)))
        
        return rmse, accuracy

def scheduler(epoch):
    # lr = 0.05 STD for short dataset
    lr = 0.03
    if epoch >= 125 and epoch < 250:
        return lr * 0.2
    elif epoch >= 250 and epoch <350:
        return lr * 0.2
    elif epoch >= 350:
        return lr * 0.2*0.2
    else:
        return lr

def correntropy_loss(y_pred, y_truth):

    mae = K.cast_to_floatx(K.mean(K.abs(y_pred - y_truth)))
    mse = K.cast_to_floatx(K.mean(K.pow(y_pred - y_truth, a=2)))
    K.set_floatx('float32')
    #corr entropy loss
    y_pred = K.cast_to_floatx(y_pred)
    y_truth = K.cast_to_floatx(y_truth)
    sigma_c = K.cast_to_floatx(0.5)
    lambda_c = K.cast_to_floatx(1.0/(2.0*sigma_c*sigma_c))
    exp_term = K.cast_to_floatx(K.exp(-lambda_c*K.pow((y_pred-y_truth), a=2)))
    G_sigma = K.cast_to_floatx((exp_term)/(np.sqrt(np.pi*2.0)*sigma_c))
    corr_loss = 1.0/(np.sqrt(np.pi*2.0)*sigma_c) - K.mean(G_sigma)
    lamb = .5
    return K.cast_to_floatx(corr_loss)

    
#print('site', site)
lstm = lstm_model()

# ----------------- Note this part is specific to the LOBO dataset ---------------------------------------------------
# ----------------- To adapt it to a new dataset a new preprocessing function needs to be used -----------------------
site = 3
# ['SLE-NF', 'IRL-SLE', 'IRL-JB', 'SLE-SF', 'SLE-SF2']
lstm.load_dataset(site)
# ----------------- End of the data loading --------------------------------------------------------------------------

rmse, mape = lstm.run()
filepath = 'models/' + str(site)
#model.save(filepath) # if you want to store the model and the reuse it
    
# clear model
del lstm
keras.backend.clear_session()
    
print('mean_accuracy', mape)
print('mean_rmse', rmse)
#print('all accuracy', mape)