import matplotlib.pyplot as plt
import numpy as np
import sys
import tensorflow as tf
from keras.models import Sequential, load_model
from keras.layers.core import Dense, Activation, Dropout, Flatten
from keras.layers import Convolution2D
from keras.layers.recurrent import LSTM, SimpleRNN, GRU
import keras as keras
from keras import backend as K
from preprocessing_farmers_2018 import preprocess_farmers2018_with_holes, normalize, normalize_with_time, normalize_min_max
from preprocessing_LOBO import preprocess_lobo
from phased_lstm_keras.PhasedLSTM import PhasedLSTM as PLSTM
from preprocessing_farmers_2019 import load_farmers2019
np.random.seed(1234)
tf.random.set_seed(35345)


class lstm_model:
    
    def __init__(self):
        
        self.input_size = 5
        self.output_size = 1
        self.hidden_units = 50
        #self.epochs = 300
        self.epochs = 600
        self.activation = 'tanh'
        self.input_horizon = 8
        self.lookahead = 5
    
        self.x_train = None
        self.y_train = None
        self.x_test = None
        self.y_test = None
    
    def load_dataset(self, site_number):

        data = preprocess_farmers2018_with_holes(site_number)
        norm_data, self.mean, self.std = normalize(data)
        if site_number == 28:
            test_dim = 5
        else: test_dim = 10
        train_steps = data.shape[0] - self.input_horizon - test_dim
        data_arranged = []
        for index in range(data.shape[0] - self.input_horizon):
            data_arranged.append(norm_data[index: index + self.input_horizon])
        data_arranged = np.array(data_arranged)
        self.x_train = data_arranged[:train_steps] # supposed to be traintepx x 12 x in_dim
        self.y_train = norm_data[self.input_horizon: train_steps + self.input_horizon, :]
        #self.y_train = np.expand_dims(y_train, axis=1)
        
        self.x_test = data_arranged[train_steps:train_steps + 5]
        self.xy_plot = data[train_steps:train_steps + self.input_horizon +5, 0]
        self.y_test = norm_data[train_steps + self.input_horizon:train_steps + self.input_horizon + 5, :]
        print('xtain', self.x_train.shape)
                    
        
    def build_lstm_layer(self, i):
        
        
        
        sites = ['SLE-NF', 'IRL-SLE', 'IRL-JB', 'SLE-SF', 'SLE-SF2']
        
        # phased lstm
        lobo_model = load_model('models/multi_output/SLE-SF2-do-te-rain-ws-hour_PhasedLSTM.h5', custom_objects={'PhasedLSTM':PLSTM})  #IRL-JB IRL-SLE SLE-SF2
        
        # lstm
        #lobo_model = load_model('models/multi_output/' + sites[i] + '-do-te-rain-ws-hour_LSTM.h5')
        
        #print(lobo_model.summary())
        #sys.exit()
        
        #lobo_model.get_layer('lstm_1').trainable = False
        #lobo_model.get_layer('dense_1').trainable = False
        
        lobo_model.layers[0].trainable = False
        #lobo_model.layers[1].trainable = False
        #lobo_model.add(Dense(units=self.input_size, name='dense_2'))
        #print(lobo_model.summary())
        #sys.exit()
        #activation = keras.layers.LeakyReLU(alpha=0.3)
        #lobo_model.add(activation)
        #optimizer = keras.optimizers.RMSprop(lr=0.002, clipnorm=1.0)
        optimizer = keras.optimizers.Adadelta(learning_rate=0.003, rho=0.999, clipnorm=1)
        #optimizer = keras.optimizers.Adadelta(learning_rate=0.003, rho=0.999, clipnorm=1) 
        #lobo_model.compile(loss="mean_squared_error", optimizer=optimizer)
        
        #lobo_model.compile(loss=correntropy_loss, optimizer=optimizer)
        lobo_model.compile(loss=correntropy_loss_plus_false_negatives, optimizer=optimizer)
        
        
        #optimizer = keras.optimizers.Adadelta(learning_rate=0.003, rho=0.999, clipnorm=1) 
        #model.compile(loss="mean_squared_error", optimizer=optimizer)
        
        return lobo_model      

    def run(self, site):
        global first
        global weights
        print (' Training LSTM  ...')
        print('xtrain', self.x_train.shape)
        print('ytrain', self.y_train.shape)

        lstmModel = self.build_lstm_layer(site)
        
        #if first:
        #    weights = lstmModel.get_weights()
        #    first = False
        #else:
        #    lstmModel.set_weights(weights)
        
        callback = tf.keras.callbacks.LearningRateScheduler(scheduler) # same in matlab
        # for short ds standard bs is 32
        lstmModel.fit(self.x_train, self.y_train, batch_size=64, epochs=self.epochs, callbacks=[callback] )
        #lstmModel.fit(self.x_train, self.y_train, batch_size=32, epochs=self.epochs)

        # testing
        print ('...... TESTING  ...')
        print('y test shape', self.y_test.shape)
        y_pred = np.zeros_like(self.y_test)
        for timestep in range(self.x_test.shape[0]):
            
            index = timestep % self.lookahead
            if index == 0:
                testInputRaw = self.x_test[timestep]
                testInputShape = testInputRaw.shape  # 12x10
                testInput = np.reshape(testInputRaw, [1, testInputShape[0], testInputShape[1]])
            else:
                testInputRaw = np.vstack((testInputRaw, y_pred[timestep-1]))
                testInputRaw = np.delete(testInputRaw, 0, axis=0)
                #print(testInputShape)
                #print('test shape', testInputRaw.shape, '  ', timestep)
                testInputShape = testInputRaw.shape
                testInput = np.reshape(testInputRaw, [1, testInputShape[0], testInputShape[1]])
                print('here lookahead')
            
            y_pred[timestep] = lstmModel.predict(testInput)
            
        y_pred_d = y_pred[:,0]*self.std + self.mean
        y_test_d = self.y_test[:,0]*self.std + self.mean
        
        #minmax norm
        #y_pred_d = y_pred*(self.std-self.mean) + self.mean
        #y_test_d = self.y_test*(self.std-self.mean) + self.mean
        
        
        rmse = np.sqrt((np.mean((np.absolute(y_pred_d - y_test_d)) ** 2)))
        accuracy = 1 - np.mean(np.abs(np.true_divide(y_test_d - y_pred_d, y_test_d)))
        
        accuracy1 = 1 - np.mean(np.abs(np.true_divide(y_test_d[0] - y_pred_d[0], y_test_d[0])))
        accuracy2 = 1 - np.mean(np.abs(np.true_divide(y_test_d[1] - y_pred_d[1], y_test_d[1])))
        accuracy3 = 1 - np.mean(np.abs(np.true_divide(y_test_d[2] - y_pred_d[2], y_test_d[2])))
        accuracy4 = 1 - np.mean(np.abs(np.true_divide(y_test_d[3] - y_pred_d[3], y_test_d[3])))
        accuracy5 = 1 - np.mean(np.abs(np.true_divide(y_test_d[4] - y_pred_d[4], y_test_d[4])))
        
        if accuracy > 0.86:
            fig, ax = plt.subplots()
            #print('dim1', self.xy_plot.shape)
            #print('y_pred_d', y_pred_d.shape)
            #print('-5', (self.xy_plot[:-5]).shape)
            #print(np.concatenate((self.xy_plot[:-5], y_pred_d)).shape)
            pred = np.concatenate((self.xy_plot[:-5], y_pred_d))
            x = np.linspace(1, self.xy_plot.shape[0], self.xy_plot.shape[0])
            #print(x.shape)
            ax.plot(x, pred, label='prediction')
            ax.plot(x, self.xy_plot, label='ground truth')
            ax.set_xlabel('time step predicted')
            ax.set_ylabel('Dissolved Oxygen (mg/l)')
            ax.legend()
            fig
            print('fig site', site)
        
        return rmse, accuracy, accuracy1, accuracy2, accuracy3, accuracy4, accuracy5

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
    print('hello')
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

def correntropy_loss_plus_false_negatives(y_pred, y_truth):

    mae = K.cast_to_floatx(K.mean(K.abs(y_pred - y_truth)))
    mse = K.cast_to_floatx(K.mean(K.pow(y_pred - y_truth, a=2)))
    print('hello')
    K.set_floatx('float32')
    #corr entropy loss
    do_pred = K.cast_to_floatx(y_pred[:, 0])
    do_truth = K.cast_to_floatx(y_truth[:, 0])
    y_pred = K.cast_to_floatx(y_pred)
    y_truth = K.cast_to_floatx(y_truth)
    
    delta = do_pred - do_truth
    is_false_positive = K.cast_to_floatx(K.greater(do_pred, do_truth))
    sigma_c = K.cast_to_floatx(0.5)
    lambda_c = K.cast_to_floatx(1.0/(2.0*sigma_c*sigma_c))
    exp_term = K.cast_to_floatx(K.exp(-lambda_c*K.pow((y_pred-y_truth), a=2)))
    G_sigma = K.cast_to_floatx((exp_term)/(np.sqrt(np.pi*2.0)*sigma_c))
    corr_loss = 1.0/(np.sqrt(np.pi*2.0)*sigma_c) - K.mean(G_sigma)
    lamb = .2
    eps = .25
    loss = (1-lamb)*corr_loss + lamb*is_false_positive*delta + eps*K.abs(delta)
    
        
    return K.cast_to_floatx(loss)

num_sites = 65  
first = True
weights = None
model_numbers = 1
rmse = np.zeros((model_numbers, num_sites))
mape = np.zeros((model_numbers, num_sites))
a1 = np.zeros(num_sites)
a2 = np.zeros(num_sites)
a3 = np.zeros(num_sites)
a4 = np.zeros(num_sites)
a5 = np.zeros(num_sites)    

for model_num in range(1):
    model_num = 4
    for site in range(num_sites):
        
        
        print('site', site)
        lstm = lstm_model()
            
        lstm.load_dataset(site+1)
        
        rmse[0, site], mape[0, site] , a1[site], a2[site], a3[site], a4[site], a5[site] = lstm.run(model_num)
        #rmse, mape = lstm.run()
        print('first', first)
    
        filepath = 'models/' + str(site + 1)
        #model.save(filepath)
        
        # clear model
        del lstm
        keras.backend.clear_session()

print('mean_accuracy', mape.mean())
print('mean_rmse', rmse.mean())
print('all accuracy', mape)
mape[0].sort()
#print('mape sorted', mape)

#print('mean_accuracy', (mape.max(axis=0)).mean())
#print('mean_rmse', (rmse.max(axis=0)).mean())
#print('all accuracy', mape.max(axis=0))
                