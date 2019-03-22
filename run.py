
from sys import platform as sys_pf
if sys_pf == 'darwin':
    import matplotlib
    matplotlib.use("TkAgg")

import time
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import os 

def getInput():

  base_x, base_y = tuple(map(int, input('Base Coordinates (x,y): ').split(',')))
  start_x, start_y = tuple(map(int, input('Starting Coordinates (x,y): ').split(',')))
  n = int(input("number of rocks: "))
  xmax = 0
  ymax = 0
  rocks = []
  for i in range(n):
    
    x, y, water = tuple(map(int, input('rock {0} details (x,y,water): '.format(i+1)).split(',')))
    
    if (water > 1 or water < 0):
      raise ValueError('The values provided for water traces are incorrect')

    xmax = max(xmax, x)
    ymax = max(xmax, y)

    rocks.append((x,y,water))

  return base_x, base_y, start_x, start_y, xmax, ymax, n, rocks


def CreateJAMFactsFile(xmax, ymax, base_x, base_y, start_x, start_y, n, rocks):

  fact_base_statement = 'FACT base {0} {1};'.format(base_x, base_y)
  fact_position_statement = 'FACT position {0} {1};'.format(start_x, start_y)
  fact_n_rocks_statement = 'FACT number_of_known_rocks {0};'.format(n)

  facts = ["FACTS: ", fact_base_statement, fact_position_statement, fact_n_rocks_statement]

  fact_rocks_statement = 'FACT known_rock {0} {1} {2} {3};'

  for i in range(len(rocks)):
    facts.append(fact_rocks_statement.format(i+1, rocks[i][0], rocks[i][1], rocks[i][2]))

  FACTS_CONTENT = '\n'.join(facts)

  filename = './experiments/facts_{0}_{1}_{2}.txt'.format(n, xmax, ymax)

  with open(filename, 'w') as file:
    file.write(FACTS_CONTENT)

  return filename

def run_jam_agent(facts_file):
  shell_command = 'java -classpath jam.jar com.irs.jam.JAM \'{0}\' \'mars_rover_agent.jam\''.format(facts_file)
  output = subprocess.run(shell_command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
  return output.stdout

def parseJAMOutput(output):
  lines = output.split('\n')
  x = lines.index('EXPLORE_ROCKS_START')
  y = lines.index('EXPLORE_ROCKS_END')
  movements = lines[x+1:y]
  l = []
  events = {}
  for i in range(len(movements)):
    if "current position" in movements[i]:
      x, y = tuple(map(int, movements[i].split(":")[1].split(",")))
      l.append((x,y))
    else:
      eventID = len(l)-1
      if eventID not in events:
        events[eventID] = []
      events[eventID].append(movements[i])
  
  return l, events

def vizualize(xmax, ymax, base_x, base_y, rocks, movements, events, save=True):

  fig, ax = plt.subplots(num=None, figsize=(10, 6), dpi=80, facecolor='w', edgecolor='k')
  fig.canvas.set_window_title('310CT Coursework')

  ln, = plt.plot([], [], 'ro', animated=True, label='Rover')
  water_rock_x = [i[0] for i in rocks if i[2]==1]
  water_rock_y = [i[1] for i in rocks if i[2]==1]
  water_sc = ax.scatter(water_rock_x,water_rock_y,s=10,c="g",marker="x",label='Water Rocks')
  ax.scatter([i[0] for i in rocks if i[2]==0],[i[1] for i in rocks if i[2]==0],s=10,c="b",marker="x",label='Empty Rocks')
  def init():
    ax.set_title("JAM Agent - Rover Simulation - {0} rocks on {1}x{2} grid".format(len(rocks), xmax, ymax))
    ax.text(base_x, base_y, 'Base ({0},{1})'.format(base_x, base_y))
    ax.set_xlim(-xmax-5, xmax+5)
    ax.set_ylim(-ymax-5, ymax+5)
    ax.legend(loc='lower right')
    return ln,

  def update(frame): 
    if frame==0:
      print('EXPLORE START\n----------------')
    ln.set_data([movements[frame][0]], [movements[frame][1]])
    if frame-1 in events:
      print("ROCK AT {0}, {1}".format(movements[frame-1][0], movements[frame-1][1]) )
      for i in events[frame-1]:
        print(i)
        if (i=='ROCK PICKED UP'):
          for i in range(len(water_rock_x)):
            if ((water_rock_x[i]==movements[frame-1][0]) and (water_rock_y[i]==movements[frame-1][1])):
              del water_rock_x[i]
              del water_rock_y[i]
              break
      print("----------------")
    
    water_sc.set_offsets(np.c_[water_rock_x,water_rock_y])

    if frame==len(movements)-1:
      print('EXPLORE END')
    return ln,water_sc,

  ani = animation.FuncAnimation(fig, update, frames= np.arange(0, len(movements)),
                      init_func=init, interval=35, blit=True, repeat=False)
  plt.grid(True)

  if save:
    ani.save(f'./{len(rocks)}_{xmax}_{ymax}_simulation.gif', fps=35, writer='imagemagick')
  else:
    plt.show()


def genRandom():
  base_x, base_y = 0,0
  start_x, start_y = 0,0
  n = random.choice(np.arange(10, 50, 10))
  xmax = random.choice(np.arange(10, 100, 10))
  ymax = xmax
  rocks = []
  for i in range(n):
    x, y, water = random.randint(-xmax, xmax), random.randint(-ymax, ymax), random.randint(0,1)
    rocks.append((x,y,water))
  return base_x, base_y, start_x, start_y, xmax, ymax, n, rocks

def writeJAMOutput(filename, output):
  outputFileName = filename.split('.txt')[0] + '_output.txt'
  with open(outputFileName, 'w') as file:
    file.write(output)

def replay(filename):
  content = ''
  with open(filename, 'r') as file:
    content = file.read()
  xmax, ymax = int(filename.split('_')[2]), int(filename.split('_')[3])
  movements, events = parseJAMOutput(content)
  base_x,base_y = movements[0][0], movements[0][1]
  rocks = []
  for i in events:
    if len(events[i])==1 and events[i][0]=="ANALYSIS COMPLETED":
      continue
    water = int(len(events[i]) > 1 and events[i][1] == "WATER FOUND")
    rocks.append(movements[i]+(water,))
  vizualize(xmax, ymax, base_x, base_y, rocks, movements, events)
  
def main(manual=False):
  base_x, base_y, start_x, start_y, xmax, ymax, n, rocks = getInput() if manual else genRandom()
  facts_file = CreateJAMFactsFile(xmax, ymax, base_x, base_y, start_x, start_y, n, rocks)
  output = run_jam_agent(facts_file)
  writeJAMOutput(facts_file, output)
  movements, events = parseJAMOutput(output)
  vizualize(xmax, ymax, base_x, base_y, rocks, movements, events)


replay('./experiments/facts_50_10_10_output.txt') #To replay an existing simulation that has already been done

#main()


      


  

