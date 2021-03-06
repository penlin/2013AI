from game import Agent
from game import Actions
from game import Directions
import random
from util import manhattanDistance
import util

class BombermanAgent( Agent ):
  def __init__( self, index ):
    self.index = index

  def getAction( self, state ):
    dist = self.getDistribution(state)
    if len(dist) == 0: 
      return Directions.STOP
    else:
      return util.chooseFromDistribution( dist )
	  
  def getDistribution(self,state):
    return util.raiseNotDefined

class RandomBomberman( Agent):
  "A ghost that chooses a legal action uniformly at random."
  
  def getAction( self, state ):
    dist = self.getDistribution(state)
    if len(dist) == 0: 
      return Directions.STOP
    else:
      return util.chooseFromDistribution( dist )  
  
  def getDistribution( self, state ):
    dist = util.Counter()
    for a in state.getLegalActions( self.index ): dist[a] = 1.0
    dist.normalize()
    return dist

class AvoidBomberman(Agent):
  def __init__(self, index = 0 , evalFn="scoreEvaluation"):
    self.evaluationFunction = util.lookup(evalFn, globals())
    self.index = index
    assert self.evaluationFunction != None
        
  def getAction(self, state):
    # Generate candidate actions
    legals = state.getLegalActions(self.index)
    if len(legals) == 1 : return legals[0]
    #if Directions.STOP in legals: legal .remove(Directions.STOP)
    legal = [action for action in legals if not action is Directions.STOP]	
	
    pos = state.getAgentPosition(self.index)
    successors = [(state.generateSuccessor(self.index,  action , True), action) for action in legal] 
    if len(successors) is 0: return random.choice(legals)
    scored = [(self.evaluationFunction(nstate,pos,Actions.directionToVector(action)), action) for nstate, action in successors]
    bestScore = min(scored)[0]
    bestActions = [pair[1] for pair in scored if pair[0] == bestScore]
    return random.choice(bestActions)
  

def scoreEvaluation(state,pos,vec):
  x,y = int(pos[0]+vec[0]),int(pos[1]+vec[1])
  return state.getBombScore(x,y) + state.getMapScore(x,y)  