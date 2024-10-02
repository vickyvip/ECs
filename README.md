# ECs
This repository is created to share the codes and inputs 

The PL.csv is the file for the power profiles. It is sampled at 30min resolution for 24 representative days of the year (2 per month)
The Bat and E files represent the battery maximum power and the energy capacity, I set them to have the same valuesm but this could be changed. 
The CAP_PV files have the values of the maximum capacity of the PV
The PV files have the actual profiles accounting with the maximul capacity of the PV - This is the value that enters as an input to the model. 
The C3 and C4 in all the files are there to differenciate between cluster 3 and cluster 4. Being C3:  a pre-designed cluster to provide high PV and Bat and C4: contaings multiple types of users, with only PV, and smaller sizes of PV and Batteries.

The scripts R_com.py and Com.py are created to run the opt model 
