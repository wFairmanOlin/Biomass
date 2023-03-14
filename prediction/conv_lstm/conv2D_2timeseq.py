import matplotlib.pyplot as plt
import numpy as np
import time
import csv
import sys
import tensorflow as tf
from keras.models import Sequential
from keras.layers.core import Dense, Activation, Dropout, Flatten
from keras.layers import Convolution2D
from keras.layers.recurrent import LSTM, SimpleRNN, GRU
from keras.layers.convolutional import Conv3D
from keras.layers.convolutional_recurrent import ConvLSTM2D
from keras.layers.normalization import BatchNormalization
import keras as keras
np.random.seed(1234)
tf.random.set_seed(35345)
from keras import backend as K
from keras.layers import Reshape


class multiLSTM:
    def __init__(self):
        self.DO_position = 1 # set DO position in the data columns
        self.lookahead = 2
        self.inputHorizon = 4 # number of time steps as input, 24 is best but slows down things
        self.stations = 5  # number of stations
        self.depth = 9  # number of columns

        # ------------ these numbers are set for plotting, since there are 5 stations, the grid of plots will be 5x1 -------
        self.rows = 1
        self.cols = 5 # print only DO
        # ------------------------------------------------------------------------------------------------------------------
        self.pixel = 4  # dimension of grid on which the stations are mapped to
        self.length = 2169  # to be set with regard to the dataset
        self.training_steps = 1800
        self.lstmModel = None
        self.xTest, self.yTest = None, None
        self.correspondences = [[1,2],[2,2],[2,0],[0,3],[1,0]]  # placing the stations into the 4x4 grid
        file_dataset = 'data/lobo_expmulti_1.csv'  # datset is timesteps x n.stations
        self.data = np.zeros((self.length, self.stations, self.depth))
        with open(file_dataset) as f:
            # data = csv.reader(f, delimiter=" ")
            for index, line in enumerate(f):
                data_line = line.split(' ')
                for site in range(self.stations):
                    self.data[index, site] = np.array(data_line[self.depth*site: self.depth*site + self.depth]).astype(float) 

        print('data_shape', self.data.shape)
        self.square_shape = [self.length, self.pixel, self.pixel, self.depth]
        self.square_data = self.make_data_square(self.data, self.square_shape)
        print('square shape', self.square_data.shape)
        
        self.min_max = []
        self.data, self.min_max = self.normalize_sites(self.data)
        self.validation_split = 0.05
        self.batchSize = 50
        activation = ['sigmoid',   "tanh",   "relu", 'linear']
        self.activation = activation[2]
        realRun = 1  # set to zero for debugging
        self.epochs, self.trainDataRate = [200, 1] if realRun else [1, 0.05]
        
        
    def make_data_square(self, data, size):
        square = np.zeros(size)
  
        # for 5 sites the image is in this way
        #       0 X 0
        #       X X X
        #       0 X 0   
        square[:, 1, 2, :] = data[:, 0, :]
        square[:, 2, 2, :] = data[:, 1, :]      
        square[:, 2, 0, :] = data[:, 2, :]
        square[:, 0, 3, :] = data[:, 3, :]
        square[:, 1, 0, :] = data[:, 4, :]

        return square
    

    def normalize_sites(self, data):
        '''normalize for all stations '''
        minmax = []
        for index in range(self.depth):
            Min = data[:, :, index].min()
            Max = data[:, :, index].max()
            data[:, :, index] = (data[:, :, index] - Min) / Max  # normalize data
            minmax.append([Min, Max])
            # means_stds.append([mean, std])
        
        #means_stds = [mean, std]
        return np.array(data), minmax

    def denormalize(self, vec):
        res = vec * self.means_stds[1] + self.means_stds[0]        #  from 0 to 1
        return res
    
    def denormalize_one_site(self, vec, site):
        res = vec * self.min_max[site][1] + self.min_max[site][0]  
        return res

    def loadData_1(self):
        # for lstm1 output xtrain ytrain
        result_lin = []
        result = []
        for index in range(len(self.data) - self.inputHorizon):
            result_lin.append(self.data[index:index + self.inputHorizon])
            result.append(self.make_data_square(self.data[index:index + self.inputHorizon], [self.inputHorizon, 4, 4, self.depth]))
            # each result contains 12xsitesxdepth elements (moving window of 12 elemnts)
        result_lin = np.array(result_lin)
        #print('res shape', result_lin.shape)
        result = np.array(result) # shape is len.seq x 12 x 4 x 4 x depth
        # print('res shape', result.shape)
        
        trainRow = int(self.training_steps * self.trainDataRate)  # n. of elements in which training is done
        X_train = result[:trainRow, :]
        y_train = self.make_data_square(self.data[self.inputHorizon:trainRow + self.inputHorizon, :, :],  [trainRow, 4, 4, self.depth])  # just the DO
        #y_train = np.expand_dims(y_train, axis=1)
        #self.xTest = result[48:48 + 361, :]
        rest = self.length - self.training_steps - self.lookahead - 10
        self.xTest = result[self.training_steps:self.training_steps + rest, :]
        self.yTest = self.make_data_square(self.data[self.training_steps + self.inputHorizon:self.training_steps + rest + self.inputHorizon, :, :],  [rest, 4, 4, self.depth])
        self.predicted = np.zeros_like(self.yTest)

        return [X_train, y_train]

  
    def buildModelLSTM(self):
        model = Sequential()
        in_nodes = out_nodes = self.stations        
        model.add(ConvLSTM2D(filters=self.depth, kernel_size=(3, 3), input_shape=(None, 4, 4, self.depth), 
                             activation = 'relu', padding='same', return_sequences=False))
        
        learning_rate = 0.001
        decay_rate = learning_rate / float(self.epochs[0])

        optimizer = keras.optimizers.RMSprop(lr=learning_rate, decay=decay_rate)
            
        model.compile(loss=custom_loss_1, optimizer=optimizer)  # try other losses like mse, mae...

        return model



    def trainLSTM(self, xTrain, yTrain):
        # train first LSTM with inputHorizon number of real input values

        lstmModel = self.buildModelLSTM()
        #yTrain = np.expand_dims(yTrain, axis=1)
        lstmModel.fit(xTrain, yTrain, batch_size=self.batchSize, nb_epoch=self.epochs, validation_split=self.validation_split)
        return lstmModel

    def test(self):
        ''' calculate the predicted values(self.predicted) '''
        for ind in range(len(self.xTest)):
            modelInd = ind % self.lookahead
            if modelInd == 0:
                testInputRaw = self.xTest[ind]
                testInput = np.expand_dims(testInputRaw, axis=0)
            else :
                testInputRaw = np.vstack((testInput, np.expand_dims(self.predicted[ind-1], axis=0)))
                testInputRaw = np.delete(testInputRaw, 0, axis=0)
                testInput = np.expand_dims(testInputRaw, axis=0)
                #print('raw shape fed', testInput.shape)

            self.predicted[ind] = self.lstmModels[modelInd].predict(testInput)


        return

    def reduced_plot(self):
        # note predict return 6 values
        # want to see max lookahead without adding input data
        predicted = np.zeros((30, self.pixel, self.pixel, self.depth))
        testInputRaw = self.xTest[0]  # inHor x pix x pix x depth
        #testInput = np.reshape(testInputRaw, [1, testInputShape[0], testInputShape[1]])
        testInput = np.expand_dims(testInputRaw, axis=0)
                    
        # rows, cols = 1, 5
        maeRmse = np.zeros((self.rows*self.cols,4))
        accuracy = np.zeros((self.rows*self.cols))

        fig, ax_array = plt.subplots(self.rows, self.cols, sharex=True, sharey=True )
        staInd = 0
        for ax in np.ravel(ax_array):
            maeRmse[staInd], accuracy[staInd] = self.reduced_drawGraphStation(staInd, predicted, visualise=1, ax=ax )
            staInd += 1
            plt.xticks([0, 10, 20, 30])#, rotation=45)

            errMean = maeRmse.mean(axis=0)
            #print ('REDUCED errMean for DO averaged: MAE =', errMean[0], 'RMSE =', 
            #   errMean[1], 'nrmse_maxMin =', errMean[2], 'nrmse_mean =', 
            #   errMean[3], 'MAPE =', accuracy.mean())

        filename = 'results/reduced_plot'
        plt.savefig('{}.png'.format(filename))
        plt.show()
        
    def reduced_drawGraphStation(self, station, predicted, visualise = 1, ax = None ):
        '''draw graph of predicted vs real values'''

        yTest = self.yTest[:30, self.correspondences[station][0], self.correspondences[station][1], self.DO_position] # 330, 4, 4, self.depth
        denormalYTestDO = self.denormalize_one_site(yTest, self.DO_position)
        denormalPredictedDO = self.denormalize_one_site(self.predicted[:30, self.correspondences[station][0], self.correspondences[station][1], self.DO_position], self.DO_position)
        accuracy = 1 - np.mean(np.abs(np.true_divide(denormalYTestDO - denormalPredictedDO, denormalYTestDO)))
        mae, rmse, nrmse_maxMin, nrmse_mean  = self.errorMeasures(denormalYTestDO, denormalPredictedDO)
        #print ('REDUCED station', station+1, 'DO', 'MAE =', mae, 'RMSE =', rmse, 'nrmse_maxMin =', nrmse_maxMin, 'nrmse_mean =', nrmse_mean )
                
        if visualise:
            if ax is None :
                fig = plt.figure()
                ax = fig.add_subplot(111)

            ax.plot(denormalYTestDO, label='Real')
            ax.plot(denormalPredictedDO, label='Predicted', color='red', alpha=0.6)
            ax.set_xticklabels([0, 10, 20, 30], rotation=40)
            

        return [mae, rmse, nrmse_maxMin, nrmse_mean], accuracy

    def errorMeasures(self, denormalYTest, denormalYPredicted):

        mae = np.mean(np.absolute(denormalYTest - denormalYPredicted))
        rmse = np.sqrt((np.mean((np.absolute(denormalYTest - denormalYPredicted)) ** 2)))
        nrsme_maxMin = 100*rmse / (denormalYTest.max() - denormalYTest.min())
        nrsme_mean = 100 * rmse / (denormalYTest.mean())

        return mae, rmse, nrsme_maxMin, nrsme_mean

    def drawGraphStation(self, station, visualise = 1, ax = None ):
        '''draw graph of predicted vs real values'''

        yTest = self.yTest[:, self.correspondences[station][0], self.correspondences[station][1], self.DO_position] # 330, 4, 4, self.depth
        denormalYTestDO = self.denormalize_one_site(yTest, self.DO_position)
        print('denormal test', self.predicted.shape) # 330 x 4 x 4 x 7
        denormalPredictedDO = self.denormalize_one_site(self.predicted[:, self.correspondences[station][0], self.correspondences[station][1], self.DO_position], self.DO_position)
        print('denormal perd', denormalPredictedDO.shape)
        accuracy = 1 - np.mean(np.abs(np.true_divide(denormalYTestDO - denormalPredictedDO, denormalYTestDO)))

        for j in range(self.depth):
            denormalYTest = self.denormalize_one_site(self.yTest[:, self.correspondences[station][0], self.correspondences[station][1], j], j)
            denormalPredicted = self.denormalize_one_site(self.predicted[:, self.correspondences[station][0], self.correspondences[station][1], j], j)
            mae, rmse, nrmse_maxMin, nrmse_mean  = self.errorMeasures(denormalYTest, denormalPredicted)
            
            if j != self.DO_position:
                print ('station', station+1, 'value', j, 'MAE =', mae, 'RMSE =', rmse, 'nrmse_maxMin =', nrmse_maxMin, 'nrmse_mean =', nrmse_mean )
            else:
                print ('station', station+1, 'DO', 'MAE =', mae, 'RMSE =', rmse, 'nrmse_maxMin =', nrmse_maxMin, 'nrmse_mean =', nrmse_mean )
                
                mae_ret = mae
                rmese_ret = rmse
                nrmse_maxMin_ret = nrmse_maxMin
                nrmse_mean_ret = nrmse_mean
                
        if visualise:
            if ax is None :
                fig = plt.figure()
                ax = fig.add_subplot(111)

                
                #fig.figsize=(100,200)

            ax.plot(denormalYTestDO[:300], label='Real')
            ax.plot(denormalPredictedDO[:300], label='Predicted', color='red', alpha=0.6)
            ax.set_xticklabels([0, 100, 200, 300], rotation=40)
            
       

        return [mae_ret, rmese_ret, nrmse_maxMin_ret, nrmse_mean_ret], accuracy

    def drawGraphAllStations(self):
        # rows, cols = 1, 5
        maeRmse = np.zeros((self.rows*self.cols,4))
        accuracy = np.zeros((self.rows*self.cols))

        fig, ax_array = plt.subplots(self.rows, self.cols, figsize=(20,10), sharex=True, sharey=True )
        staInd = 0
        for ax in np.ravel(ax_array):
            maeRmse[staInd], accuracy[staInd] = self.drawGraphStation(staInd, visualise=1, ax=ax)
            staInd += 1
        plt.xticks([0, 100, 200, 300])#, rotation=45)

        print('maeRMS', maeRmse.shape)
        errMean = maeRmse.mean(axis=0)
        print ('errMean for DO averaged: MAE =', errMean[0], 'RMSE =', 
               errMean[1], 'nrmse_maxMin =', errMean[2], 'nrmse_mean =', 
               errMean[3], 'MAPE =', accuracy.mean())

        filename = 'results/300_test_every_2_hours'
        plt.savefig('{}.png'.format(filename))
        #plt.savefig('{}.png'.format(filename))
        plt.show()

        return

    def run(self):
        #  training
        xTrain, yTrain = self.loadData_1()
        
        print (' Training LSTM 1 ...')
        print('xtrain', xTrain.shape)
        print('ytrain', yTrain.shape)
        self.lstmModels = self.trainLSTM(xTrain, yTrain, 1)
        # testing
        print ('...... TESTING  ...')
        self.test()
        
        self.drawGraphAllStations()
        
def custom_loss_1(y_pred, y_truth):
    # in this case the DO is the first site
    # data dimension  is
    # -------------------------------------------------------
    # training_samples x n. sites
    # -------------------------------------------------------

    mae = K.mean(K.abs(y_pred - y_truth))
    
    DO_err = K.mean(K.abs(y_pred[:,:,:, 1] - y_truth[:,:,:, 1]))
    
                            
    lamb = .3
    return mae + lamb*DO_err

DeepForecast = multiLSTM()
DeepForecast.run()
DeepForecast.reduced_plot()
