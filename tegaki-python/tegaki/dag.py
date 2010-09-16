# -*- coding: utf-8 -*-

# Copyright (C) 2010 The Tegaki project contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Contributors to this file:
# - Mathieu Blondel

"""
Directed Acyclic Graph
"""

from dictutils import *

class Node(object):
    """
    A node can have several children and several parents.
    However, children can't be the parent of their parents (no cycle).
    """
    def __init__(self, value=None, parents={}):
        self._child_nodes = SortedDict()
        self._value = value
        self._parent_nodes = SortedDict(parents)
        self._depth = 0

    # value

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def get_value_string(self):
        return self._value

    def __repr__(self):
        value = self.get_value_string()
        if value is None:
            return "Node()"
        else:
            return "Node(%s)" % value

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return hash(self._value)

    # children

    def get_n_child_nodes(self):
        return len(self._child_nodes)

    def is_leaf_node(self):
        return self.get_n_child_nodes() == 0

    def get_child_nodes(self):
        return self._child_nodes.values()

    def get_child_node(self, value):
        return self._child_nodes[value]

    def has_child_node(self, node):
        return self.has_child_node_value(node.get_value())

    def has_child_node_value(self, value):
        return value in self._child_nodes

    def set_child_node(self, node):
        node.set_parent_node(self)
        self._child_nodes[node.get_value()] = node

    def set_child_nodes(self, nodelist):
        self._child_nodes = SortedDict()
        for node in nodelist:
            self.set_child_node(node)

    # parent

    def has_parent_node(self, parent):
        return parent.get_value() in self._parent_nodes

    def has_ancestor_node(self, parent):
        for node, depth in parent.depth_first_search():
            if node == self:
                return True
        return False

    def get_parent_nodes(self):
        return self._parent_nodes.values()

    def get_parent_node(self, value):
        return self._parent_nodes[value]

    def set_parent_node(self, node):
        self._parent_nodes[node.get_value()] = node

    def set_parent_nodes(self, nodelist):
        self._parent_nodes = SortedDict()
        for node in nodelist:
            self.set_parent_node(node)

    def get_generative_sequence(self):
        """
        One sequence of nodes that led to this node.
        """
        seq = []
        node = self

        while len(node.get_parent_nodes()) > 0:
            seq.insert(0, node)
            node = node.get_parent_nodes()[0]

        seq.insert(0, node)

        return seq

    # depth

    def get_depth(self):
        return self._depth

    def set_depth(self, depth):
        self._depth = depth

    def update_depths(self):
        for node, depth in self.depth_first_search():
            node.set_depth(depth)

    def get_max_depth(self):
        return max(depth for node, depth in self.depth_first_search())

    def get_n_nodes(self):
        return len(dict((node,1) for node, dep in self.depth_first_search()))

    # search

#     def depth_first_search(self):
#         yield self, 0 # root
#         for child in self.get_child_nodes():
#             for node, depth in child.depth_first_search():
#                 stop = (yield node, depth+1)
#                 if stop is not None:
#                     yield None
#                     break

    def depth_first_search(self):
        it = self.depth_first_search_args()
        for node, depth, visited, args in it:
            yield node, depth
            it.send(((),True))

    def depth_first_search_unique(self):
        d = {}
        for node, depth in self.depth_first_search():
            if not node in d:
                d[node] = 1
                yield node, depth

    def depth_first_search_args(self, *args):
        stack = [(self,0,args)]
        d = {}

        def _add_children(node):
            for child in node.get_child_nodes():
                for node_, depth in child.depth_first_search():
                    d[node_] = 1

        while len(stack) > 0:
            node,depth,args = stack.pop()
            d[node] = 1
            args, continue_ = (yield node, depth, len(d), args)
            yield None

            if continue_:
                stack += [(n,depth+1,args) for n in reversed(node.get_child_nodes())
                                           if not n in d]
            else:
                _add_children(node)

#     def breadth_first_search(self):
#         yield self, 0 # root
#         last = self
#
#         for node, depth in self.breadth_first_search():
#             for child in node.get_child_nodes():
#
#                 yield child, depth+1
#                 last = child
#
#             if last == node:
#                 raise StopIteration

    # iterative version
    def breadth_first_search(self):
        yield self, 0 # root
        stack = [self]

        while len(stack) > 0:
            node = stack.pop()

            for i, child in enumerate(node.get_child_nodes()):
                yield child, 0
                stack.insert(0, child)

    @classmethod
    def child_nodes_all(cls, nodes):
        children = []
        for node in nodes:
            children += node.get_child_nodes()
        return children


    def tree(self):
        """
        Returns a tree representation in text format.
        """
        s = ""

        for node, depth in self.depth_first_search():
            s += ("  " * depth) + str(node) + "\n"

        return s

if __name__ == "__main__":
    treestring = \
"""
          R
       /  |  \
      1   2  3
    / |   |  \
    4 5   6  9
         / \
        7  8
"""
    node7 = Node(7)
    node8 = Node(8)
    node6 = Node(6)
    node6.set_child_nodes([node7, node8])

    node4 = Node(4)
    node5 = Node(5)
    node1 = Node(1)
    node1.set_child_nodes([node4, node5])

    node2 = Node(2)
    node2.set_child_nodes([node6])

    node3 = Node(3)
    node9 = Node(9)
    node3.set_child_nodes([node9])

    root = Node()
    root.set_child_nodes([node1, node2, node3])

    def print_and_assert(prefix, got, expected):
        print prefix
        try:
            assert(got == expected)
            print got
        except AssertionError:
            print "got: ", got
            print "but expected: ", expected

    print "tree:\n", root.tree()

    print_and_assert("depth-first",
        [(n.get_value(), d) for n,d in list(root.depth_first_search())],
        [(None, 0), (1, 1), (4, 2), (5, 2), (2, 1), (6, 2), (7, 3), (8, 3), (3,
            1), (9, 2)])

    print_and_assert("breadth-first",
        [n.get_value() for n,d in list(root.breadth_first_search())],
        [None, 1, 2, 3, 4, 5, 6, 9, 7, 8])

    depth1_nodes = Node.child_nodes_all([root])
    print "child nodes of root: ", depth1_nodes

    print "parent of parent of 8: ", node8.get_parent_nodes()[0].get_parent_nodes()[0]
    print "generative sequence of 8: ", node8.get_generative_sequence()

    assert(node8.get_depth() == 0)
    assert(node6.get_depth() == 0)
    assert(node2.get_depth() == 0)
    assert(root.get_depth() == 0)

    root.update_depths()

    assert(node8.get_depth() == 3)
    assert(node6.get_depth() == 2)
    assert(node2.get_depth() == 1)
    assert(root.get_depth() == 0)

    print "depth-first search with args"
    it = root.depth_first_search_args(0)
    for node, depth, visited, args in it:
        print node, depth, visited, args
        it.send(((args[0]+1,),True))

    print "depth-first search unique"
    it = root.depth_first_search_unique()
    for node, depth in it:
        print node, depth
