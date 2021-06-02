import numpy as np
from scipy.special import softmax as sm
from wine_data import norm_wine, wine_labels
from copy import deepcopy

class Synapses():
    def __init__(self, pre, post, freq, f_width=0.3, weight=1.):
        self.pre = pre
        self.post = post
        self.freq = freq
        self.f_width = f_width
        self.weight = weight

    def response(self, input):
        return self.weight * max(1. - abs((input - self.freq) / self.f_width), 0)

class Neuron():
    def __init__(self, neuron_label, connections):
        self.neuron_label = neuron_label
        self.synapses = {}
        self.synapse_count = len(connections)
        for pre in connections:
            freq = connections[pre]
            self.synapses[pre] = []
            self.synapses[pre].append(Synapses(pre+'0', neuron_label, freq))
            
    def add_connection(self, pre, freq, weight=1.):
        self.synapse_count += 1
        if pre not in self.synapses:
            self.synapses[pre] = []
        self.synapses[pre].append(Synapses(pre+'{}'.format(len(self.synapses[pre])),
                                           self.neuron_label, freq,
                                           weight=weight))
            
    def add_multiple_connections(self, connections):
        for pre in connections:
            freq = connections[pre]
            if pre not in self.synapses:
                self.synapses[pre] = []
            self.synapses[pre].append(Synapses(pre+'{}'.format(len(self.synapses[pre])),
                                               self.neuron_label, freq))
            self.synapse_count += 1
        
    def response(self, activations):
        if not self.synapse_count:
            return 0.
        response = 0.
        for pre in activations:
            freq = activations[pre]
            if pre in self.synapses:
                for synapse in self.synapses[pre]:
                    response += synapse.response(freq)
        return response / self.synapse_count
        
class Network():
    def __init__(self, number_of_classes, seed_class, seed_features, error_threshold=0.1):
        self.error_threshold = error_threshold
        self.neurons = {}
        self.number_of_classes = number_of_classes
        # add seed neuron
        self.neurons['seed{}'.format(seed_class)] = Neuron('seed{}'.format(seed_class), 
                                                          self.convert_wine_to_activations(seed_features))
        # add outputs
        for output in range(number_of_classes):
            self.add_neuron({}, 'out{}'.format(output))
        # connect seed neuron to seed class
        self.neurons['out{}'.format(seed_class)].add_connection('seed{}'.format(seed_class),
                                                               freq=1.)
        self.hidden_neuron_count = 1
        self.layers = 2
    
    def add_neuron(self, connections, neuron_label=''):
        if neuron_label == '':
            neuron_label = 'n{}'.format(self.hidden_neuron_count)
            self.hidden_neuron_count += 1
        self.neurons[neuron_label] = Neuron(neuron_label, connections)
        return neuron_label
        #### find a way to know whether you need to add a layer
        # for pre in connections:
        #     if 'in' not in pre
        
    def connect_neuron(self, neuron_label, connections):
        self.neurons[neuron_label].add_multiple_connections(connections)
        
    def response(self, activations):
        for i in range(self.layers):
            for neuron in self.neurons:
                response = self.neurons[neuron].response(activations)
                activations[self.neurons[neuron].neuron_label] = response
        return activations
        
    def convert_wine_to_activations(self, wine):
        water = {}
        for idx, ele in enumerate(wine):
            water['in{}'.format(idx)] = ele
        return water

    def remove_output_neurons(self, activations):
        neural_activations = {}
        for neuron in activations:
            if 'out' not in neuron:
                neural_activations[neuron] = activations[neuron]
        return neural_activations

    def error_driven_neuro_genesis(self, activations, output_error):
        if np.max(np.abs(output_error)) > self.error_threshold:
            activations = self.remove_output_neurons(activations)
            neuron_label = self.add_neuron(activations)
            for output, error in enumerate(output_error):
                if abs(error) > self.error_threshold:
                    self.neurons['out{}'.format(output)].add_connection(neuron_label,
                                                                        freq=1.,
                                                                        weight=-error)


def calculate_error(correct_class, activations, wine_count):
    output_activations = np.zeros(3)
    error = np.zeros(3)
    one_hot_encoding = np.zeros(3)
    one_hot_encoding[correct_class] = 1
    for output in range(3):
        output_activations[output] = activations['out{}'.format(output)]
    # softmax = sm(output_activations)
    softmax = output_activations
    if sum(softmax) > 0.:
        choice = softmax.argmax()
    else:
        choice = -1
    for output in range(3):
        error[output] += softmax[output] - one_hot_encoding[output]

    print("Error for test ", wine_count, " is ", error)
    print("output \n"
          "{} - 1:{} - sm:{}\n"
          "{} - 2:{} - sm:{}\n"
          "{} - 3:{} - sm:{}".format(one_hot_encoding[0], output_activations[0], softmax[0],
                                       one_hot_encoding[1], output_activations[1], softmax[1],
                                       one_hot_encoding[2], output_activations[2], softmax[2]))
          # "{} - 3:{}\n".format(int(label == 0), activations['out0'],
          #                      int(label == 1), activations['out1'],
          #                      int(label == 2), activations['out2']))
    return error, choice


epochs = 200
sensitivity_width = 0.1
error_threshold = 0.01
seed_class = 0
winet = Network(3, wine_labels[seed_class], norm_wine[seed_class], error_threshold=error_threshold)
all_incorrect_classes = []

for epoch in range(epochs):
    activations = {}
    wine_count = 0
    correct_classifications = 0
    incorrect_classes = []
    for wine, label in zip(norm_wine, wine_labels):
        activations = winet.convert_wine_to_activations(wine)
        activations = winet.response(activations)
        print("Epoch ", epoch, "/", epochs)
        error, choice = calculate_error(label, activations, wine_count)
        print("neuron count", len(activations) - len(wine) - 3)
        if label == choice:
            correct_classifications += 1
            print("CORRECT CLASS WAS CHOSEN\n")
        else:
            print("INCORRECT CLASS WAS CHOSEN\n")
            incorrect_classes.append('({}) {}: {}'.format(wine_count, label, choice))
            winet.error_driven_neuro_genesis(activations, error)
        wine_count += 1
    print(incorrect_classes)
    all_incorrect_classes.append(incorrect_classes)
    print('Epoch', epoch, '/', epochs, '\nClassification accuracy: ',
          correct_classifications/len(wine_labels))
    for ep in all_incorrect_classes:
        print(len(ep), "-", ep)








    
