#!/usr/bin/env python3


import torch
import tictactoe as ttt

board_size = 3
n_spaces = board_size**2
dimensions = [10,10,9]

def activation(z):
	return torch.tanh(z)


def infere(state,parameters):

	# converts to flatt one hot encoding
	in_state = torch.tensor(state)
	flatt = in_state.flatten()
	z = torch.zeros(3,n_spaces)
	z[flatt,torch.arange(n_spaces)] = 1.
	z = z.flatten()


	# runs through layers
	for layer_index in range(len(dimensions)):
		z = activation(parameters[layer_index][0]+
			       torch.matmul(parameters[layer_index][1],z))

	return z

# softmax layer for the policy network
def policy_head(state,parameters):

	out = infere(state,parameters)
	exp_out = torch.exp(out)
	return torch.argmax(exp_out/torch.sum(exp_out))


#weight initialization
def get_weights():
	parameters = []

	for i in range(len(dimensions)):
		size = dimensions[i]
		if i == 0:
			prev_size = n_spaces*3
		else:
			prev_size = dimensions[i-1]
		biases = torch.randn(size)
		weights = torch.randn((size,prev_size))

		parameters.append([biases,weights])

	return parameters

def get_coords(n,size):

	x = n//size
	y = n%size
	return x,y


def play_episode(Game,agent_parameters):

	states_batch = [[],[]]
	actions_batch = [[],[]]
	rewards_batch = [[],[]]
	game_len = 0
	player = False
	over = False

	while game_len <= Game.size**2 and not(over):

		action = policy_head(Game.board,agent_parameters[int(player)])
		x,y = get_coords(action.item(),Game.size)
		allowed = Game.setField(x,y)

		states_batch[int(player)].append(Game.board)
		actions_batch[int(player)].append(action.item())

		# checks outcome
		res =  Game.checkboard()
		if res:

			rewards_batch[int(player)] = [1.] * len(states_batch[int(player)])
			rewards_batch[int(not(player))] = [-1.] * len(states_states_batch[int(not(player))])

			over = True

		if not(allowed):

			rewards_batch[int(player)] = [-1.]*len(states_batch[int(player)])
			rewards_batch[int(not(player))] = [0.]*len(states_batch[int(not(player))])

			over = True

		# catches draws
		if game_len == Game.size**2:

			rewards_batch[0] = [0.] * len(states_batch[0])
			rewards_batch[1] = [0.] * len(states_batch[1])

			over = True

		game_len += 1
		player = not(player)

	Game.reset()


	return states_batch,actions_batch,rewards_batch


def get_training_batch(Game,agent_parameters,batch_size):

	collected = 0

	states = [[],[]]
	actions = [[],[]]
	rewards = [[],[]]

	while collected <= (batch_size+Game.size**2):
		states_batch,actions_batch,rewards_batch = play_episode(Game,agent_parameters)

		states[0] += states_batch[0]
		states[1] += states_batch[1]

		actions[0] += actions_batch[0]
		actions[1] += actions_batch[1]

		rewards[0] += rewards_batch[0]
		rewards[1] += rewards_batch[1]

		collected += len(rewards_batch)//2

	states[0] = states[0][:batch_size]
	states[1] = states[1][:batch_size]

	actions[0] = actions[0][:batch_size]
	actions[1] = actions[1][:batch_size]

	rewards[0] = rewards[0][:batch_size]
	rewards[1] = rewards[1][:batch_size]

	return states,actions,rewards


if __name__ == '__main__':

	Game = ttt.Tictactoe(3,3)
	batch_size = 400

	#weight initialization
	agent_parameters = [get_weights() for x in range(2)]


	for Epoch in range(10):
		states,actions,rewards = get_training_batch(Game,agent_parameters,batch_size)