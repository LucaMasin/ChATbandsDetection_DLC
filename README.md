# ChATbandsDetection_DLC
ChATbands detection based on DeepLabCut

### Installation instructions
Todo 

### Usage instructions
Todo

### Data
ON and OFF bands were manually labeled using Fiji. A 2D standard deviation filter (21x21 pixels) was applied to all slices.

### Worflow
Subimages are extracted from the each slice with a sliding window approach. The step size controls the density of predictions along the x-axis. The model predicts the location of ON- and OFF bands in the center column of each subimage. Lastly, predictions for each subimage are remapped to the original slices along. 

### DeepLabCut modifications
Masks are applied to the location prediction outputs and to the loss function. Location refinement along the x-axis was removed.  
- Mask on bodypart location prediction in the deconvolutional layer limits predictions to the center column of the image. 
- Mask on loss function (same as on bodypart location) ensures loss is only calculated for the center column of the image. 

