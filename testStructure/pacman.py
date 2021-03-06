# pacman.py
# ---------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

"""
Pacman.py holds the logic for the classic pacman game along with the main
code to run a game.  This file is divided into three sections:

  (i)  Your interface to the pacman world:
          Pacman is a complex environment.  You probably don't want to
          read through all of the code we wrote to make the game runs
          correctly.  This section contains the parts of the code
          that you will need to understand in order to complete the
          project.  There is also some code in game.py that you should
          understand.

  (ii)  The hidden secrets of pacman:
          This section contains all of the logic code that the pacman
          environment uses to decide who can move where, who dies when
          things collide, etc.  You shouldn't need to read this section
          of code, but you can if you want.

  (iii) Framework to start a game:
          The final section contains the code for reading the command
          you use to set up the game, then starting up a new game, along with
          linking in all the external parts (agent functions, graphics).
          Check this section out to see all the options available to you.

To play your first game, type 'python pacman.py' from the command line.
The keys are 'a', 's', 'd', and 'w' to move (or arrow keys).  Have fun!
"""
from game import GameStateData
from game import Game
from game import Directions
from game import Actions
from game import Map
from util import nearestPoint
from util import manhattanDistance
import util, layout
import sys, types, time, random, os

###################################################
# YOUR INTERFACE TO THE PACMAN WORLD: A GameState #
###################################################

class GameState:
  """
  A GameState specifies the full game state, including the food, capsules,
  agent configurations and score changes.

  GameStates are used by the Game object to capture the actual state of the game and
  can be used by agents to reason about the game.

  Much of the information in a GameState is stored in a GameStateData object.  We
  strongly suggest that you access that data via the accessor methods below rather
  than referring to the GameStateData object directly.

  Note that in classic Pacman, Pacman is always agent 0.
  """

  ####################################################
  # Accessor methods: use these to access state data #
  ####################################################

  def updateState(self, actions):
    """
    Returns the successor state after the actions of all active agents.
    """
    # Check that successors exist  
    if self.isWin() or self.isLose(): raise Exception('it is terminal state now.')

    self.data.clear()
	
    for agentIndex in range(len(actions)):
      if self.data._eaten[agentIndex] > 0:
        BombermanRules.applyAction( self, actions[agentIndex], agentIndex )

    self.minusOneFrame()
    for counter,position,power,index in self.data.bombs:
      if counter == self.getFramesUntilEnd():
        self.bombExplode(self.data.bombs,position,power)
        if index >= 0:
          self.getAgentState(index).recoverABomb()
    self.data.bombs = [b for b in self.data.bombs if (b[0] != self.getFramesUntilEnd())]

    self.updateBombScore()	
    self.updateMapScore()
	
    self.data.score = self.data._eaten[0]

  
  def getLegalActions( self, agentIndex=0 ):
    """
    Returns the legal actions for the agent specified.
    """
    if self.isWin() or self.isLose(): return []
    return BombermanRules.getLegalActions( self , agentIndex)

  def generateSuccessor( self, agentIndex, action , force = False):
    """
    Returns the successor state after the specified agent takes the action.
    """
    # Check that successors exist
    if self.isWin() or self.isLose(): raise Exception('Can\'t generate a successor of a terminal state.')

    # Copy current state
    state = GameState(self)

    # Let agent's logic deal with its action's effects on the board

    #state.data._eaten = [False for i in range(state.getNumAgents())]
    if state.data._eaten[agentIndex] > 0:
      BombermanRules.applyAction( state, action, agentIndex )

    if force or ( agentIndex == state.getNumAgents() - 1):
      state.minusOneFrame()
      for counter,position,power,index in state.data.bombs:
        if counter == state.getFramesUntilEnd():
          state.bombExplode(state.data.bombs,position,power)
          state.getAgentState(index).recoverABomb()
      state.data.bombs = [b for b in state.data.bombs if (b[0] != state.getFramesUntilEnd())]

    state.updateBombScore()	
    state.updateMapScore()	
    # Time passes
    state.data.scoreChange += -TIME_PENALTY # Penalty for waiting around

    # Resolve multi-agent effects
    #GhostRules.checkDeath( state, agentIndex )

    # Book keeping
    state.data._agentMoved = agentIndex
    state.data.score += state.data.scoreChange
    return state

  def getAgentPosition( self, agentIndex ):
    return self.data.agentStates[agentIndex].getPosition()
	
  def getAgentState(self, agentIndex):
    return 	self.data.agentStates[agentIndex]
	
  def getNumAgents( self ):
    return len( self.data.agentStates )

  def getScore( self ):
    return self.data.score

  def getMapScore(self,x,y=None):
    if y is None:
      try : x,y = x
      except: raise  'incomprehensible coordinates' 
    return self.data.MapScore[x][y]
	
  def getBombScore(self,x,y=None):
    if y is None:
      try : x,y = x
      except: raise  'incomprehensible coordinates' 
    return self.data.BombScore[x][y]
	  
  def hasWall(self, x, y):
    return self.data.map.isWall((x,y))

  def isLose( self ):
    return (self.getNumAgents() == 1 and self.data._eaten[0] == 0) or (self.data._eaten.count(0) == self.getNumAgents())

  def isWin( self ):
    return ( self.getNumAgents()!=1 and self.data._eaten.count(0) is self.getNumAgents()-1 ) 

  def getFramesUntilEnd(self ):
    return self.data.FramesUntilEnd

  def minusOneFrame( self ):
    self.data.FramesUntilEnd = self.data.FramesUntilEnd - 1
    return self.data.FramesUntilEnd

  def layABomb(self,agentIndex,pos):
    self.data._bombLaid.append(pos)
    self.data.map.add_bomb(pos)
    self.getAgentState(agentIndex).minusABomb()
    self.data.bombs.append( (self.data.FramesUntilEnd - BOMB_DURATION , 
                             pos, self.getAgentState(agentIndex).getBombPower() , agentIndex ) )

	
  def bombExplode(self,bombs, position, power):
    x_int, y_int = position
    if not self.data.map.isBomb(position): return
    self.data._bombExplode.append(position)
    self.data.map.remove_object(position)
    fired = [] 
    for i in range(len(self.data._fire)):
       fired +=  self.data._fire[i]
	
    if not position in fired:
      self.checkDie(position)
      self.data._fire[0].append(position)
      fired.append(position)
    for vec in [ v for dir, v in Actions._directionsAsList if ( not dir in  [ Actions.LAY ,Directions.STOP])]:
      isbreak = False
      i = 0
      dx, dy = vec
      next_y, next_x = y_int,x_int
      while not isbreak and i < power:
          i=i+1
          next_y = int(next_y + dy)
          next_x = int(next_x + dx)
          pos = (next_x,next_y)
          if pos in fired: continue
          if self.data.map.isEmpty(pos):
            self.checkDie(pos)
            self.data._fire[i].append(pos)
            fired.append(pos)
          elif self.data.map.isBlock(pos):
            isbreak = True
            self.data._blockBroken.append(pos)
            res = self.data.map.remove_object(pos)
            self.data._fire[i].append(pos)
            fired.append(pos)
            if res != None:
              self.data._itemDrop.append((next_x,next_y,res))
          elif self.data.map.isWall(pos):
            isbreak = True
          elif self.data.map.isItem(pos):
            self.data._itemEaten.append(pos)
            self.data.map.remove_object(pos)
            self.data._fire[i].append(pos)
            fired.append(pos)
            self.checkDie(pos)
          elif self.data.map.isBomb(pos):
            self.checkDie(pos)
            self.data._fire[i].append(pos)
            fired.append(pos)
            bombSweep = [(idx,bomb) for idx,bomb in enumerate(bombs) if (pos in bomb ) and (bomb[0] < self.data.FramesUntilEnd-int(BOMB_DURATION/10)) ]
            if len(bombSweep) is 1:
              bombs[bombSweep[0][0]] = (self.data.FramesUntilEnd-int(BOMB_DURATION/10),)+bombSweep[0][1][1:]
                
            
  def checkDie(self,position):
    x,y = position
    for index,agent in enumerate(self.data.agentStates):
      if self.data._eaten[index] is 0 : continue
      sx,sy = agent.getPosition()
      sx,sy = round(sx),round(sy)
      if manhattanDistance(position,(sx,sy)) <= 0.5:
        self.data._eaten[index] -= 1 
        agent.configuration = agent.start		

  def updateBombScore(self):
    # The change to the BombScore:
    self.data.BombScore.data = [[0 for y in range(self.data.map.height)] for x in range(self.data.map.width)]
    for counter, pos, power, index in self.data.bombs:
      score = self.calBombScore(counter)
      self.data.BombScore[pos[0]][pos[1]] += score
      isbreak = False
      for vec in [v for dir, v in Actions._directionsAsList if ( not dir in  [ Actions.LAY ,Directions.STOP])]:
        isbreak = False
        i = 0
        dx,dy = vec
        next_x,next_y = pos
        while not isbreak and i < power:
          i += 1
          next_x = int(next_x+dx)
          next_y = int(next_y+dy)
          if self.data.map.isBlock((next_x,next_y)) or self.data.map.isWall((next_x,next_y)):
            isbreak = True
          else :
            self.data.BombScore[next_x][next_y] += score-i/5.0

  def updateMapScore(self):
    self.data.MapScore.data = [[0 for y in range(self.data.map.height)] for x in range(self.data.map.width)]
    for x in range(self.data.map.width):
      for y in range(self.data.map.height):
        if not self.data.map.isBlocked((x,y)) or self.data.map.isBomb((x,y)):
          main = [self.data.map.isBlocked((row,col)) for row,col in [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]]
          second = [self.data.map.isBlocked((row,col)) for row,col in [(x+1,y+1),(x-1,y+1),(x+1,y-1),(x-1,y-1)]]
          self.data.MapScore[x][y] = ( main.count(True)*1 + second.count(True)*0.4 )
          if main.count(True) == 4: self.data.MapScore[x][y] = 100
          if self.data.map.isBomb((x,y)): self.data.MapScore[x][y] += 1
		  
  def calBombScore(self, counter):
    if self.getFramesUntilEnd() - 1 == counter:  # next frame would explode
		return 100
		
    return 3*(BOMB_DURATION - (self.getFramesUntilEnd() - counter))

  def getTotalLives(self, indexes):
    return sum([self.data._eaten[index] for index in indexes])
	
  #############################################
  #             Helper methods:               #
  # You shouldn't need to call these directly #
  #############################################

  def __init__( self, prevState = None):
    """
    Generates a new state by copying information from its predecessor.
    """
    if prevState != None: # Initial state
      self.data = GameStateData(prevState.data)
    else:
      self.data = GameStateData()

  def deepCopy( self ):
    state = GameState( self )
    state.data = self.data.deepCopy()
    return state

  def __eq__( self, other ):
    """
    Allows two states to be compared.
    """
    return self.data == other.data

  def __hash__( self ):
    """
    Allows states to be keys of dictionaries.
    """
    return hash( self.data )

  def __str__( self ):

    return str(self.data)

  def initialize( self, layout, numAgents=1000 , timeout = 3000, life = 5 ):
    """
    Creates an initial game state from a layout array (see layout.py).
    """
    self.data.initialize(layout, numAgents, timeout, life , BOMB_DURATION)

############################################################################
#                     THE HIDDEN SECRETS OF PACMAN                         #
#                                                                          #
# You shouldn't need to look through the code in this section of the file. #
############################################################################

SCARED_TIME = 40    # Moves ghosts are scared
COLLISION_TOLERANCE = 0.7 # How close ghosts must be to Pacman to kill
TIME_PENALTY = 1 # Number of points lost each round

BOMB_DURATION = 20

class ClassicGameRules:
  """
  These game rules manage the control flow of a game, deciding when
  and how the game starts and ends.
  """
  
  def __init__(self, timeout=3000, life = 5 , team_mode = False):
    global BOMBERMAN_LIFE
    self.timeout = timeout
    self.BOMBERMAN_LIFE = life
    self.team_mode = team_mode

  def newGame( self, layout, Agents, display, quiet = False):
    if not self.team_mode:
      agents = Agents[:layout.getNumAgents()]#[pacmanAgent] + ghostAgents[:layout.getNumGhosts()]
    else:
	  teams = Agents
    initState = GameState()
    if not self.team_mode:
      initState.initialize( layout, len(agents) ,self.timeout, self.BOMBERMAN_LIFE)
    else:
      initState.initialize( layout, sum([team.getNumOfAgents() for team in teams]) ,self.timeout, self.BOMBERMAN_LIFE)
    if not self.team_mode:
      game = Game(agents, display, self)
    else:
      game = Game(teams,display,self)
    game.state = initState
    self.initialState = initState.deepCopy()
    self.quiet = quiet
    return game

  def process(self, state, game):
    """
    Checks to see whether it is time to end the game.
    """
    if self.team_mode:
      if state.getTotalLives(game.agents[0].agentIndex) == 0:
        self.lose(state, game)
      elif sum([state.getTotalLives(team.agentIndex) for team in game.agents[1:]]) == 0:
        self.win(state, game)
    else:		
      if state.isWin(): self.win(state, game)
      if state.isLose(): self.lose(state, game)
	  
    if state.getFramesUntilEnd() < 0: game.gameOver = True


  def win( self, state, game ):
    if not self.quiet: print "Bomberman victorious! Score: %d" % state.data.score
    game.gameOver = True

  def lose( self, state, game ):
    if not self.quiet: print "Bomberman lose! Score: %d" % state.data.score
    game.gameOver = True

  def getProgress(self, game):
    return float(game.state.getNumFood()) / self.initialState.getNumFood()

  def agentCrash(self, game, agentIndex):
    """if agentIndex == 0:
      print "Pacman crashed"
    else:
      print "A ghost crashed" """
    print 'A bomberman(',agentIndex,') crashed'

  def getMaxTotalTime(self, agentIndex):
    return self.timeout

  def getMaxStartupTime(self, agentIndex):
    return self.timeout

  def getMoveWarningTime(self, agentIndex):
    return self.timeout

  def getMoveTimeout(self, agentIndex):
    return self.timeout

  def getMaxTimeWarnings(self, agentIndex):
    return 0

class BombermanRules:
  """
  These functions govern how pacman interacts with his environment under
  the classic game rules.
  """
  PACMAN_SPEED=1

  def getLegalActions( state , index = 0):
    """
    Returns a list of possible actions.
    """

    legal = Actions.getPossibleActions( state.getAgentState(index).configuration, state.data.map )
    if Actions.LAY in legal and not state.getAgentState(index).hasBomb():
        legal.remove(Actions.LAY)
    return legal
  getLegalActions = staticmethod( getLegalActions )

  def applyAction( state, action, index ):
    """
    Edits the state to reflect the results of the action.
    """
    legal = BombermanRules.getLegalActions( state, index)
    if action not in legal:
      print ("Illegal action " + str(action) + " with agentIndex " + str(index) + ' and legals:' + str(legal))
      #action = random.choice(legal)
      if Directions.STOP in legal: action = Directions.STOP
      else : action =random.choice(legal)

    agentState = state.data.agentStates[index]

    # Update Configuration
    vector = Actions.directionToVector( action, agentState.getSpeed() )
    agentState.configuration = agentState.configuration.generateSuccessor( vector )
    # Eat
    next = agentState.configuration.getPosition()
    nearest = nearestPoint( next )
    if manhattanDistance( nearest, next ) <= 0.5 :
      # consume item
      BombermanRules.consume( nearest, state, index )
    # Lay bomb
    if action is Actions.LAY:
      state.layABomb(index,nearest)
	  
  applyAction = staticmethod( applyAction )

  def consume( position, state , index):

    if state.data.map.isItem(position):
      #apply item effect
      state.getAgentState(index).applyItemEffect(state.data.map.get_data(position))
      # remove the item
      state.data.map.remove_object(position)
      state.data._itemEaten.append(position)
  consume = staticmethod( consume )

#############################
# FRAMEWORK TO START A GAME #
#############################

def default(str):
  return str + ' [Default: %default]'

def parseAgentArgs(str):
  if str == None: return {}
  pieces = str.split(',')
  opts = {}
  for p in pieces:
    if '=' in p:
      key, val = p.split('=')
    else:
      key,val = p, 1
    opts[key] = val
  return opts

def readCommand( argv ):
  """
  Processes the command used to run pacman from the command line.
  """
  from optparse import OptionParser
  usageStr = """
  USAGE:      python pacman.py <options>
  EXAMPLES:   (1) python pacman.py
                  - starts an interactive game
              (2) python pacman.py --layout smallClassic --zoom 2
              OR  python pacman.py -l smallClassic -z 2
                  - starts an interactive game on a smaller board, zoomed in
  """
  parser = OptionParser(usageStr)

  parser.add_option('-n', '--numGames', dest='numGames', type='int',
                    help=default('the number of GAMES to play'), metavar='GAMES', default=1)
  parser.add_option('-l', '--layout', dest='layout',
                    help=default('the LAYOUT_FILE from which to load the map layout'),
                    metavar='LAYOUT_FILE', default='testClassic')
  parser.add_option('-p', '--agent', dest='agent',
                    help=default('the agent TYPE in the pacmanAgents module to use'),
                    metavar='TYPE', default='KeyboardAgent')
  parser.add_option('-t', '--textGraphics', action='store_true', dest='textGraphics',
                    help='Display output as text only', default=False)
  parser.add_option('-q', '--quietTextGraphics', action='store_true', dest='quietGraphics',
                    help='Generate minimal output and no graphics', default=False)
  """ parser.add_option('-g', '--ghosts', dest='ghost',
                    help=default('the ghost agent TYPE in the ghostAgents module to use'),
                    metavar = 'TYPE', default='RandomGhost') """
  parser.add_option('-k', '--numAgent', type='int', dest='numAgent',
                    help=default('The maximum number of Agents to use'), default=1)
  parser.add_option('-z', '--zoom', type='float', dest='zoom',
                    help=default('Zoom the size of the graphics window'), default=1.0)
  parser.add_option('-f', '--fixRandomSeed', action='store_true', dest='fixRandomSeed',
                    help='Fixes the random seed to always play the same game', default=False)
  parser.add_option('-r', '--recordActions', action='store_true', dest='record',
                    help='Writes game histories to a file (named by the time they were played)', default=False)
  parser.add_option('--replay', dest='gameToReplay',
                    help='A recorded game file (pickle) to replay', default=None)
  parser.add_option('-a','--agentArgs',dest='agentArgs',
                    help='Comma separated values sent to agent. e.g. "opt1=val1,opt2,opt3=val3"')
  parser.add_option('-x', '--numTraining', dest='numTraining', type='int',
                    help=default('How many episodes are training (suppresses output)'), default=0)
  parser.add_option('--frameTime', dest='frameTime', type='float',
                    help=default('Time to delay between frames; <0 means keyboard'), default=0.1)

  parser.add_option('--timeout', dest='timeout', type='int',
                    help=default('Maximum length of time an agent can spend computing in a single game'), default=3000)
					
  parser.add_option('-m', dest='manual', type='int',
                    help=default('The index number of the manual agent [or -1 for all AI]'), default=0)
					
  parser.add_option('-c','--team',dest='team',metavar='TYPE',
                    help=default('The team competeness mode'), default=None)
					
  parser.add_option('--life', dest='life', type='int',
                    help=default('The life number of an agent'), default=5)	
					
  options, otherjunk = parser.parse_args(argv)
  if len(otherjunk) != 0:
    raise Exception('Command line input not understood: ' + str(otherjunk))
  args = dict()

  # Fix the random seed
  if options.fixRandomSeed: random.seed('cs188')

  # Choose a layout
  args['layout'] = layout.getLayout( options.layout )
  if args['layout'] == None: raise Exception("The layout " + options.layout + " cannot be found")

  # Choose a Pacman agent
  noKeyboard = options.gameToReplay == None and (options.textGraphics or options.quietGraphics)
  agentType = loadAgent(options.agent, noKeyboard)
  agentOpts = parseAgentArgs(options.agentArgs)
  if options.numTraining > 0:
    args['numTraining'] = options.numTraining
    if 'numTraining' not in agentOpts: agentOpts['numTraining'] = options.numTraining
  if options.numAgent > 1 and options.manual >= 0 :
    from keyboardAgents import KeyboardAgent
    args['agents'] = [ agentType(i) for i in range(0,options.manual)] + [ agentType(i) for i in range(options.manual+1,options.numAgent)]
    args['agents'].insert(options.manual, KeyboardAgent(options.manual))
  elif options.numAgent > 1:
    args['agents'] =[ agentType(i) for i in range(options.numAgent)] # Instantiate Pacman with agentArgs
  else:
    args['agents'] = [agentType(0)]
    
  if not options.team is None:
    if options.numAgent%2: raise Exception("For team mode, agents number must be even!")
    args['teamMode'] = True
    TeamagentType = loadAgent(options.team, noKeyboard)
    args['team'] = [TeamagentType(0,args['agents'][0:options.numAgent:2],range(0,options.numAgent,2)), 
	                 TeamagentType(1,args['agents'][1:options.numAgent:2],range(1,options.numAgent,2))]
    
  
  
  # Don't display training games
  if 'numTrain' in agentOpts:
    options.numQuiet = int(agentOpts['numTrain'])
    options.numIgnore = int(agentOpts['numTrain'])

  # Choose a display format
  if options.quietGraphics:
      import textDisplay
      args['display'] = textDisplay.NullGraphics()
  elif options.textGraphics:
    import textDisplay
    textDisplay.SLEEP_TIME = options.frameTime
    args['display'] = textDisplay.PacmanGraphics()
  else:
    import graphicsDisplay
    args['display'] = graphicsDisplay.PacmanGraphics(options.zoom, frameTime = options.frameTime)
  args['numGames'] = options.numGames
  args['record'] = options.record
  args['timeout'] = options.timeout


  # Special case: recorded games don't use the runGames method or args structure
  if options.gameToReplay != None:
    print 'Replaying recorded game %s.' % options.gameToReplay
    import cPickle
    f = open(options.gameToReplay)
    try: recorded = cPickle.load(f)
    finally: f.close()
    recorded['display'] = args['display']
    replayGame(**recorded)
    sys.exit(0)

  if options.life > 0:
    args['life'] = options.life
  else:
    args['life'] = 5
	
  return args

def loadAgent(agent, nographics):
  # Looks through all pythonPath Directories for the right module,
  pythonPathStr = os.path.expandvars("$PYTHONPATH")
  if pythonPathStr.find(';') == -1:
    pythonPathDirs = pythonPathStr.split(':')
  else:
    pythonPathDirs = pythonPathStr.split(';')
  pythonPathDirs.append('.')

  for moduleDir in pythonPathDirs:
    if not os.path.isdir(moduleDir): continue
    moduleNames = [f for f in os.listdir(moduleDir) if f.endswith('gents.py')]
    for modulename in moduleNames:
      try:
        module = __import__(modulename[:-3])
      except ImportError:
        continue
      if agent in dir(module):
        if nographics and modulename == 'keyboardAgents.py':
          raise Exception('Using the keyboard requires graphics (not text display)')
        return getattr(module, agent)
  raise Exception('The agent ' + agent + ' is not specified in any *Agents.py.')

def replayGame( layout, actions, display ):
    import pacmanAgents, ghostAgents
    rules = ClassicGameRules()
    agents = [pacmanAgents.GreedyAgent()] + [ghostAgents.RandomGhost(i+1) for i in range(layout.getNumGhosts())]
    game = rules.newGame( layout, agents[0], agents[1:], display )
    state = game.state
    display.initialize(state.data)

    for action in actions:
      # Execute the action
      state = state.generateSuccessor( *action )
      # Change the display
      display.update( state.data )
      # Allow for game specific conditions (winning, losing, etc.)
      rules.process(state, game)

    display.finish()

def runGames( layout, agents, display, numGames, record, numTraining = 0, timeout=3000 , life = 5 , teamMode = False , team = None ):
  import __main__
  __main__.__dict__['_display'] = display

  rules = ClassicGameRules(timeout,life,teamMode)
  games = []

  for i in range( numGames ):
    beQuiet = i < numTraining
    if beQuiet:
        # Suppress output and graphics
        import textDisplay
        gameDisplay = textDisplay.NullGraphics()
        rules.quiet = True
    else:
        gameDisplay = display
        rules.quiet = False
    if teamMode:game = rules.newGame( layout, team, gameDisplay, beQuiet)
    else: game = rules.newGame( layout, agents, gameDisplay, beQuiet)
    game.run()
    if not beQuiet: games.append(game)

    if record:
      import time, cPickle
      fname = ('recorded-game-%d' % (i + 1)) +  '-'.join([str(t) for t in time.localtime()[1:6]])
      f = file(fname, 'w')
      components = {'layout': layout, 'actions': game.moveHistory}
      cPickle.dump(components, f)
      f.close()

  if numGames > 1:
    scores = [game.state.getScore() for game in games]
    wins = [game.state.isWin() for game in games]
    winRate = wins.count(True)/ float(len(wins))
    print 'Average Score:', sum(scores) / float(len(scores))
    print 'Scores:       ', ', '.join([str(score) for score in scores])
    print 'Win Rate:      %d/%d (%.2f)' % (wins.count(True), len(wins), winRate)
    print 'Record:       ', ', '.join([ ['Loss', 'Win'][int(w)] for w in wins])

  return games

if __name__ == '__main__':
  """
  The main function called when pacman.py is run
  from the command line:

  > python pacman.py

  See the usage string for more details.

  > python pacman.py --help
  """
  args = readCommand( sys.argv[1:] ) # Get game components based on input
  runGames( **args )

  # import cProfile
  # cProfile.run("runGames( **args )")
  pass