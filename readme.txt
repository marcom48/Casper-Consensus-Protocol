COMP90020 Term Report
Marco Marasco 834482
Austen McClernon 834063

This application simulates a blockchain environment that implements the Casper Finality consensus protocol for determining finality of blocks generated in the blockchain.

Below are high-level descriptions of each of the files. Each file contains further commenting and explanations of its logic.

simulation.py
File is used to simulate and visualise a blockchain that implements the Casper protocol.
Executed by "python simulation.py", a blockchain is simulated and plotted into a subdirectory "simulation_blockchains".
To configure the simulation, please see helper/parameters.py, subsection "Simulation Parameters".

fault_tests.py
File is used to test the performance of a blockchain that implements the Casper protocol under varying failure scenarios.
Executed by "python fault_tests.py <test_type>", where <test_type> is one of:
* latency
* network
* byzantine

Each fault type scenario is tested and the results are plotted in a subdirectory "fault_graphs".
To configure the tests, please see helper/parameters.py, subsection "Fault Test Parameters".



casper/block.py
This file contains the class structure of blocks for the blockchain.

casper/caspervalidator.py
Contains the instantiated class for validators that implement the Casper protocol.

casper/network.py
File contains the code for the network simulated, and the structure of vote messages sent through
the network.

casper/node.py
Contains an abstract class for validators in the network, with essential requirements for validators.



helper/hash_gen.py
Contains function to generate pseudo-random hash values.

helper/parameters.py
Consists of various parameters used to configure simulations and tests for the application.

helper/visualisation.py
Contains functions used to plot blockchains and graphs.


