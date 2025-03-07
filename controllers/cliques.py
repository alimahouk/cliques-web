import networkx as nx

from app import models
from app.constants import ProtocolKey
from controllers import connectivity, crypto


def clique_exists(users=None, cliqueID=None):
        if users is None and cliqueID is None:
                raise ValueError(
                        "cliques.clique_exists(2): both parameters are null")
        
        if cliqueID is not None:
                if models.Clique.get(cliqueID) is not None:
                        return True
                else:
                        return False
        else:
                cliqueID = group_id(users)
                if models.Clique.get(cliqueID) is not None:
                        return True
                else:
                        return False


# This function calculates all the cliques the given user belongs
# to.
# NOTE: this is not being pulled from the DB, so use this function
# sparingly.
def cliques_all(userID):
        connections = models.UserConnection.all_get(userID, raw=True)
        graph = graph_make([userID] + connections)
        return nx.algorithms.clique.cliques_containing_node(graph, userID)


def cliques_break(user1, user2):
        if user1 == user2:
                raise ValueError(
                        "cliques.cliques_break(2): both parameters refer to the same user")

        # Deactivate the exclusive subgroup that these two users belong to.
        subgroup = [user1, user2]
        subgroupID = group_id(subgroup)
        models.CliqueMembership.activate(subgroupID, active=False)

        # Deactivate the supergroup and reactivate the subgroups.
        # ATTENTION: make sure the subgroup doesn't exist within another supergroup
        # before activating it!
        cliques = cliques_including(user1, user2)
        for clique in cliques:
                cliqueID = group_id(clique)
                subgroupUser1 = [member for member in clique if member != user2]
                subgroupUser2 = [member for member in clique if member != user1]
                if subgroupUser1:
                        activate = True
                        cliquesUser1 = cliques_get(user1, stripUser=True)
                        for cliqueUser1 in cliquesUser1:
                                # Preprocessing to prepare the groups for comparison.
                                members = cliqueUser1[ProtocolKey.MEMBERS]
                                members = [member for member in members if member != user2]
                                strippedSubgroupUser1 = [member for member in subgroupUser1 if member != user1]
                                # A subgroup is activated iff it is a strict subset (i.e. not equal to the other set).
                                if set(strippedSubgroupUser1) < set(members):
                                        activate = False
                                        break
                        
                        if activate:
                                subgroupIDUser1 = group_id(subgroupUser1)
                                models.CliqueMembership.activate(subgroupIDUser1)
                if subgroupUser2:
                        activate = True
                        cliquesUser2 = cliques_get(user2, stripUser=True)
                        for cliqueUser2 in cliquesUser2:
                                members = cliqueUser2[ProtocolKey.MEMBERS]
                                members = [member for member in members if member != user1]
                                strippedSubgroupUser2 = [member for member in subgroupUser2 if member != user2]
                                if set(strippedSubgroupUser2) < set(members):
                                        activate = False
                                        break

                        if activate:
                                subgroupIDUser2 = group_id(subgroupUser2)
                                models.CliqueMembership.activate(subgroupIDUser2)

                models.CliqueMembership.activate(cliqueID, active=False)


def cliques_get(userID, raw=True, stripUser=True):
        if userID is None:
                raise ValueError("cliques.cliques_get(1): userID argument is null")

        cliques = models.Clique.all_get(userID)
        for clique in cliques:
                cliqueID = clique[ProtocolKey.CLIQUE_ID]
                members = models.CliqueMembership.all_get(cliqueID, raw=raw)
                if stripUser:
                        if raw:
                                members = [member for member in members if member != userID]
                        else:
                                members = [member for member in members if member[ProtocolKey.USER_ID] != userID]
                
                clique[ProtocolKey.MEMBERS] = members
                
        return cliques


def cliques_including(user1, user2):
        if user1 == user2:
                raise ValueError("cliques.cliques_including(2): both parameters refer to the same user")

        # 1) Form the base group.
        base = [user1, user2]
        mutuals = connectivity.mutual_connections(user1, user2)
        # 2) Get the full graph.
        graph = graph_make(base + mutuals)
        # 3) Find all maximum cliques.
        cliquesMax = nx.algorithms.clique.find_cliques(graph)
        cliquesValid = []
        for clique in cliquesMax:
                if user1 in clique and user2 in clique:
                        cliquesValid.append(clique)
        return cliquesValid


def cliques_make(user1, user2):
        if user1 == user2:
                raise ValueError("cliques.cliques_make(2): both parameters refer to the same user")

        # These two users will first form their own exclusive subgroup.
        subgroup = [user1, user2]
        subgroupID = group_id(subgroup)
        models.Clique.make(subgroupID)
        models.CliqueMembership.make(subgroupID, subgroup, active=False)
        # Deactivate the two subgroups that each of the two parties
        # currently belong to and put them all in a new supergroup.
        cliques = cliques_including(user1, user2)
        for clique in cliques:
                cliqueID = group_id(clique)
                models.Clique.make(cliqueID)
                models.CliqueMembership.make(cliqueID, clique)

                possibleSubgroupIDs = []
                possibleSubgroups = subgroups(clique)
                for subgroup in possibleSubgroups:
                        subgroupID = group_id(subgroup)
                        possibleSubgroupIDs.append(subgroupID)
                        models.Clique.make(subgroupID)
                        models.CliqueMembership.make(subgroupID, subgroup, active=False)
                        models.CliqueMembership.activate(subgroupID, active=False)
                
                models.CliqueRelationship.make(cliqueID, possibleSubgroupIDs)
                #subgroupUser1 = [member for member in clique if member != user2]
                #subgroupUser2 = [member for member in clique if member != user1]

                #if subgroupUser1:
                #	subgroupIDUser1 = group_id(subgroupUser1)
                #	models.CliqueMembership.activate(subgroupIDUser1, active=False)
                #if subgroupUser2:
                #	subgroupIDUser2 = group_id(subgroupUser2)
                #	models.CliqueMembership.activate(subgroupIDUser2, active=False)

                #models.Clique.make(cliqueID)
                #models.CliqueMembership.make(cliqueID, clique)
                ## Store references to all possible subgroups.
                #possibleSubgroups = subgroups(clique)
                #models.CliqueRelationship.make(cliqueID, possibleSubgroups)


def graph_make(users, makeClique=False):
        if users is None:
                raise ValueError("cliques.graph_make(2): users parameter is null")

        net = nx.Graph()
        # makeClique simply connects all the users to all other users in the list,
        # i.e. it does not hit the DB.
        if makeClique:
                for index, user in enumerate(users):
                        if index < len(users)-1:
                                for case in users[index+1:]:
                                        net.add_edge(user, case)
        else:
                for index, user in enumerate(users):
                        connections = models.UserConnection.all_get(user, raw=True)
                        if index < len(users)-1:
                                for case in users[index+1:]:
                                        if case in connections:
                                                net.add_edge(user, case)
        return net


def group_id(users):
        # GROUP ID GENERATION
        # This method expects a list of ints.
        #
        # 1) Sort the list in ascending order.
        # 2) Turn the list into a comma-separated string
        # 3) SHA256-hash the string.
        sortedList = sorted(users)
        preparedStr = ",".join(str(i) for i in sortedList)
        return crypto.sha256_str(preparedStr)


# Returns a list of all possible subgroups for the given group.
def subgroups(users, raw=False):
        graph = graph_make(users, makeClique=True)
        possibilities = []
        userSet = set(users) # Turn the list into a set for order-agnostic comparisons.
        for clique in nx.algorithms.clique.enumerate_all_cliques(graph):
                if len(clique) > 1 and userSet != set(clique):
                        if raw:
                                # Return a list of possible group IDs.
                                cliqueID = group_id(clique)
                                possibilities.append(cliqueID)
                        else:
                                # Return a list of members of possible groups.
                                possibilities.append(clique)
        return possibilities


def superclique_exists(userID, cliqueID):
        # Useful when trying to figure out if a user is
        # a part of a superclique that includes the given
        # clique.
        members = models.CliqueMembership.all_get(cliqueID, raw=True)
        for memberID in members:
                # We're just checking if this user is connected to all the clique members.
                if not connectivity.connection_exists(userID, memberID):
                        return False

        return True
