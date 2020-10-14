

Sentence = tp.NewType("Sentence", list[str])


PrintedTree = namedtuple('PrintedTree', ('sentences', 'left', 'right'))


class TreeError(Exception):
    def __init__(self, msg: str, *args, **kwargs):
        logger.error(msg)
        super().__init__(msg, *args, **kwargs)


class Tree(object):

    def __init__(self, start_statement: str, branch_name: str = 'A', parent: Tree = None, child_l: Tree = None,
                 child_r: Tree = None, leaves_dict: dict[str, Tree] = None, closed: tp.Union[None, tuple[int]] = None, used: tp.Set[int] = set()):
        """The representation of one node in a tree; non-diverging rules add to this one's statement list. It's accounted for in the interface

        :param start_statement: The first statement to insert into the node
        :type start_statement: str
        :param branch_name: Name of the branch; use `gen_name` on the parent to find the name, defaults to 'A'
        :type branch_name: str, optional
        :param parent: Parent node
        :type parent: Tree, optional
        :param child_l: Left child of the node
        :type child_l: Tree, optional
        :param child_r: Right child of the node
        :type child_r: Tree, optional
        :param leaves_dict: If the tree has a dict of leaves it can be stored here; when not provided system will create an empty dict
        :type leaves_dict: dict[str, Tree], optional
        :param closed: Stores information about the closing sentences of this leaf, defaults to None
        :type closed: tuple[int], optional
        :param used: A set for storing IDs of sentences which can't be used again in this branch, defaults to an empty set
        :type used: tp.Set[int], optional
        """
        self.name = branch_name
        self.statements = [start_statement]
        self.parent = parent
        assert (child_l and child_r) or (
            not child_l and not child_r), "One child"
        self.left = child_l     # TODO: zaimplementować to jako self.children, a nie left i right
        self.right = child_r
        self.closed = closed
        self.used = used
        if leaves_dict is None:
            leaves_dict = dict()
        leaves_dict[branch_name] = self
        self.leaves = leaves_dict

    # Technical

    @staticmethod
    def _distalph(letter_a: str, letter_b: str) -> int:
        """Calculates distance between two letters"""
        assert len(letter_a) == 1 and len(
            letter_b) == 1, "_distalph only checks chars"
        return alphabet.index(letter_a) - alphabet.index(letter_b)

    def gen_name(self) -> tuple[str]:
        """Generates two possible names for the children of this node"""
        if self.parent:
            dist = self._distalph(self.name, self.parent.getchildren()[
                                  0].name) + self._distalph(self.name, self.parent.getchildren()[-1].name)
            assert dist != 0
            new = abs(dist)//2
            if dist < 0:
                if self.leaves:
                    assert not alphabet[new] in self.leaves.keys()
                return self.name, alphabet[new]
            else:
                if self.leaves:
                    assert not alphabet[25-new] in self.leaves.keys()
                return alphabet[25-new], self.name
        else:
            return 'A', 'Z'

    # Tree reading

    def getroot(self) -> Tree:
        if self.parent:
            return self.parent.getroot()
        else:
            return self

    def getchildren(self) -> tuple[Tree, Tree]:
        if not self.left:  # Trees with only one child aren't supported
            return None
        else:
            return self.left, self.right

    def getbranch(self) -> tuple[str, bool]:
        """Returns all the sentences in this node's branch and information about branch's closure"""
        return self._getbranch(), self.closed

    def _getbranch(self):
        """Returns all the sentences in this node's branch; `getbranch` is recommended"""
        if self.parent:
            return self.parent._getbranch() + self.statements
        else:
            return self.statements

    def gettree(self):
        """Creates recursively a named tuple with the sentences"""
        if not self.left:  # Trees with only one child aren't supported
            return PrintedTree(sentences=self.statements, left=None, right=None)
        else:
            return PrintedTree(sentences=self.statements, left=self.left.get_tree(), right=self.right.get_tree())

    def getleaves(self, *names: tp.Iterable[str]) -> list[Tree]:
        """Returns all or chosen leaves (if names are provided as args)

        :return: List of the leaves
        :rtype: list[Tree]
        """
        if names:
            return [self.leaves.get(i, None) for i in names]
        else:
            return list(self.leaves.values())

    def getopen(self, *names: tp.Iterable[str]) -> tp.Iterator[Tree]:
        """Returns all or chosen open leaves (if names are provided as args)

        :return: Iterator of the leaves
        :rtype: tp.Iterator[Tree]
        """
        return (i for i in self.getleaves(*names) if not i.closed)

    def getneighbour(self, left_right: str) -> tp.Union[Tree, None]: 
        #TODO:  Verify whether it makes sense algorithmically
        #       Maybe separete a method for leaves and the rest of the tree 
        min_dist = 100
        obj_w_min = None
        if left_right.upper() in ('R', 'RIGHT'):
            for i in self.leaves.items():
                dist = self._distalph(i[0], self.name)
                if dist > 0 and dist < min_dist:
                    min_dist = dist
                    obj_w_min = i[1]
            return obj_w_min
        elif left_right.upper() in ('L', 'LEFT'):
            for i in self.leaves.items():
                dist = self._distalph(self.name, i[0])
                if dist > 0 and dist < min_dist:
                    min_dist = dist
                    obj_w_min = i[1]
            return obj_w_min
        else:
            raise EngineError(f"'{left_right}' is not a valid direction")
            return None

    # Tree modification

    @EngineLog
    def _add_statement(self, statements: tp.Union[str, list[str]]) -> None:
        """Adds statement(s) to the node

        :param statements: statement(s)
        :type statements: str or list[str]
        """
        if isinstance(statements, str):
            self.statements.append(statements)
        else:
            self.statements.extend(statements)

    @EngineLog
    def _add_child(self, l_statements: tp.Union[str, list[str]], r_statements: tp.Union[str, list[str]]):
        """Adds statements as children of the node

        :param l_statements: Statement(s) to be added to the left child
        :type l_statements: str, list[str]
        :param r_statements: Statement(s) to be added to the right child
        :type r_statements: str, list[str]
        """
        names = self.gen_name()
        if isinstance(l_statements, str):
            self.left = Tree(
                l_statements, names[0], self, leaves_dict=self.leaves, closed=self.closed, used=self.used.copy())
        else:
            self.left = Tree(
                l_statements[0], names[0], self, leaves_dict=self.leaves, closed=self.closed, used=self.used.copy())
            self.left.append((l_statements[1:],))
        if isinstance(r_statements, str):
            self.right = Tree(
                r_statements, names[1], self, leaves_dict=self.leaves, closed=self.closed, used=self.used.copy())
        else:
            self.right = Tree(
                r_statements[0], names[1], self, leaves_dict=self.leaves, closed=self.closed, used=self.used.copy())
            self.right.append((r_statements[1:],))

    def append(self, statements: tuple):
        """Prefered way of adding new statements. Use a tuple with tuples filled with sentences.
        Every tuple of strings is interpreted as a new branch. If there is only one statement it will be added to the existing node. 

        :param statements: Statements grouped into branches
        :type statements: tuple[tuple[str]]
        :raises TreeError: Too much branches to append
        """
        assert isinstance(statements, tuple)
        if len(statements) == 1:
            self._add_statement(*statements)
        elif len(statements) == 2:
            self._add_child(*statements)
        else:
            raise TreeError(
                f'Trying to append {len(statements)} branches to the tree')

    def close(self, contradicting: int, num_self: int = None) -> None:
        """Close the 

        :param contradicting: ID of the colliding sentence
        :type contradicting: int
        :param num_self: Use if you already have ID of the colliding sentence
        :type num_self: int, optional
        """
        if num_self:
            self.closed = (num_self, contradicting)
        else:
            self.closed = (len(self.getbranch())-1, contradicting)

    def add_used(self, used: int) -> None:
        """
        Adds the statement ID to the used statements set
        Should only be used after non-reusable rules
        """
        assert used not in self.used
        self.used.add(used)
