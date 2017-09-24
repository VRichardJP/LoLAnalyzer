Here are some info about the models I provide. If you want to use one of these models, don't forget to edit BestPicks.py with the correct parameters (defined at the end of the file)

#### ABR_TJMCS_DenseUniform_5_1024.h5: 
servers: all  
leagues: challenger, master, diamond  
patches: 7.16, 7.17 (up to 22/09/17)  
number of games: ~750,000  
testing accuracy (overall): 53.49  
testing accuracy (full draft): 55.57  
size: 74.8 MB  
parameters:  

```
m = Modes.ABR_TJMCS_Mode(['7.16', '7.17'])
n = Networks.DenseUniform(mode=m, n_hidden_layers=5, NN=1024, dropout=0.2, batch_size=1000, report=1)
```
