Put the data used for training in the data/training folder. Each training data consists of a .tif/.tiff file and the excel files containing the labeled ON and OFF positions of the chatbands.
Put the data used for inference in the data/inference folder. This should be .tif/.tiff files.
The resulting predictions of the model on the inference data will be put in the results folder.

Follow these steps for training and inference:
1. Open a command prompt and type 'cd chatbands'. This will change the directory to the chatbands directory.
2. Type 'source activate mousetracker'. This will make the terminal use the mousetracker conda environment.
3. Type 'jupyter notebook'. A webpage should open up.
4a. If you want to the model from scratch, open the 'chatbands_detection_training.ipynb' file on the webpage an follow the steps. To execute a step, use the Shift-Enter keys.
4b. If you want to use a trained model on new data, open the 'chatbands_detection_inference.ipynb' file and follow the steps. To execute a step, use the Shift-Enter keys. 
