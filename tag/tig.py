import itertools


#===================================================================================================
# TIG trees
#===================================================================================================
class NonTerminal(object):
    def __init__(self, name):
        self.name = name
    def __call__(self, *children):
        return Node(self, children)
    def __str__(self):
        return str(self.name)

class Foot(object):
    def __init__(self, nonterm):
        self.nonterm = nonterm
    def __str__(self):
        return "%s*" % (self.nonterm,)
    
class Node(object):
    def __init__(self, root, children):
        self.root = root
        self.children = list(children)
    def __str__(self):
        return "%s" % (self.root,)
    
    def traverse_leaves(self):
        for child in self.children:
            if isinstance(child, Node):
                for n in child.traverse_leaves():
                    yield n
            else:
                yield child

LEFT_AUX = 1
RIGHT_AUX = 2


class TIG(object):
    def __init__(self, init_trees, aux_trees):
        self.init_trees = set(init_trees)
        self.aux_trees = set(aux_trees)
        
        for t in self.init_trees:
            if any(isinstance(n, Foot) for n in t.traverse_leaves()):
                raise TypeError("Initial trees must not contain foot leaves", t)

        for t in self.aux_trees:
            leaves = list(t.traverse_leaves())
            if isinstance(leaves[0], Foot):
                t.direction = RIGHT_AUX
                non_feet_leaves = leaves[1:]
                foot = leaves[0]
            elif isinstance(leaves[-1], Foot):
                t.direction = LEFT_AUX
                non_feet_leaves = leaves[:-1]
                foot = leaves[-1]
            else:
                raise TypeError("An Aux tree must contain a foot", t)
            if any(isinstance(n, Foot) for n in non_feet_leaves):
                raise TypeError("The foot of an Aux tree must be either leftmost or rightmost", t)
            if foot.nonterm != t.root:
                raise TypeError("Foot must be labeled the same as the root", t)

        self.by_symbol_init = {}
        for t in self.init_trees:
            if t.root not in self.by_symbol_init:
                self.by_symbol_init[t.root] = []
            self.by_symbol_init[t.root].append(t)

        self.by_symbol_aux = {}
        for t in self.aux_trees:
            if t.root not in self.by_symbol_aux:
                self.by_symbol_aux[t.root] = []
            self.by_symbol_aux[t.root].append(t)
    
    def get_init_trees(self, symbol):
        return self.by_symbol_init.get(symbol, ())

    def get_aux_trees(self, symbol):
        return self.by_symbol_aux.get(symbol, ())

    def handle_left_aux(self, chart, s):
        if s.dot != 0:
            return
    
        # Left Aux (2)
        for t in self.get_aux_trees(s.tree.root):
            if t.direction == LEFT_AUX:
                chart.add(State(t, 0, s.j, s.j, s.prev), s, "LA2")
        
        # Left Aux (3)
        for s2 in chart:
            if (hasattr(s2.tree, "direction") and s.tree.root == s2.tree.root and 
                    s2.is_complete() and s2.i == s.j and s2.tree.direction == LEFT_AUX):
                chart.add(State(s.tree, 0, s.i, s2.j, s2), s2, "LA3")
    
    def handle_scan(self, chart, s, token):
        if s.is_complete():
            return
        
        if isinstance(s.next(), str):
            # Scan (4)
            if s.next() == token:
                chart.add(State(s.tree, s.dot+1, s.i, s.j+1, s.prev), s, "SC4")
            
            # Scan (5)
            if s.next() == "":
                chart.add(State(s.tree, s.dot+1, s.i, s.j, s.prev), s, "SC5")
    
        # Scan (6)
        if isinstance(s.next(), Foot):
            chart.add(State(s.tree, s.dot+1, s.i, s.j, s.prev), s, "SC6")
    
    def handle_substitution(self, chart, s):
        if s.is_complete() or not isinstance(s.next(), NonTerminal):
            return
        
        r = s.next()
        
        # Substitution (7)
        for t in self.get_init_trees(r):
            chart.add(State(t, 0, s.j, s.j, s.prev), s, "SU7")
    
        # Substitution (8)
        for s2 in chart:
            if s2.tree.root == r and s2.is_complete() and s2.i == s.j and s2.tree in self.init_trees:
                chart.add(State(s.tree, s.dot + 1, s.i, s2.j, s.prev), s2, "SU8")
    
    def handle_subtree(self, chart, s):
        if s.is_complete() or not isinstance(s.next(), Node):
            return
    
        r = s.next()
        
        # Subtree (9)
        chart.add(State(r, 0, s.j, s.j, s.prev), s, "ST9")
        
        # Subtree (10)
        for s2 in chart:
            if s2.tree == r and s2.is_complete() and s2.i == s.j:
                chart.add(State(s.tree, s.dot+1, s.i, s2.j, s.prev), s2, "ST10")
    
    def handle_right_aux(self, chart, s):
        if not s.is_complete():
            return
    
        # Right Aux (11)
        for t in self.get_aux_trees(s.tree.root):
            if t.direction == RIGHT_AUX:
                chart.add(State(t, 0, s.j, s.j, s.prev), s, "RA11")
    
        # Right Aux (12)
        for s2 in chart:
            if (hasattr(s2.tree, "direction") and s2.tree.root == s.tree.root and 
                    s2.is_complete() and s2.i == s.j and s2.tree.direction == RIGHT_AUX):
                chart.add(State(s.tree, s.dot, s.i, s2.j, s2), s2, "RA12")
    
    
    def parse(self, start_symbol, tokens):
        chart = Chart()
        tokens = [None] + list(tokens)
        for tree in self.get_init_trees(start_symbol):
            chart.add(State(tree, 0, 0, 0), None, "IN1")
        
        while True:
            for s in chart:
                self.handle_left_aux(chart, s)
                self.handle_scan(chart, s, tokens[s.j+1] if s.j+1 < len(tokens) else None)
                self.handle_substitution(chart, s)
                self.handle_subtree(chart, s)
                self.handle_right_aux(chart, s)
            
            if not chart.commit():
                # no more changes, we're done
                break
        
        matches = []
        for s in chart:
            if (s.is_complete() and s.tree.root == start_symbol and s.i == 0 and 
                    s.j == len(tokens) - 1 and s.tree in self.init_trees):
                matches.append(s)
        return matches, chart

#===================================================================================================
# parser state
#===================================================================================================
class State(object):
    def __init__(self, tree, dot, i, j, prev = None):
        self.tree = tree
        self.dot = dot
        self.i = i
        self.j = j
        self.prev = prev
    def __hash__(self):
        return hash((self.tree, self.dot, self.i, self.j))
    def __eq__(self, other):
        return (self.tree, self.dot, self.i, self.j) == (other.tree, other.dot, other.i, other.j)
    def __ne__(self, other):
        return not (self == other)
    def __repr__(self):
        prod = [u"%s\u2193" % (c,) if isinstance(c, NonTerminal) else str(c) 
            for c in self.tree.children]
        prod.insert(self.dot, u"\u00b7")
        #if self.prev:
        #    prod.insert(0, "<" +" ".join([str(n) for n in self.prev.tree.children]) + ">")
        return u"(%s \u2192 %s, %r:%r)" % (self.tree.root, " ".join(prod), self.i, self.j)
    def next(self):
        if self.is_complete():
            return None
        return self.tree.children[self.dot]
    def is_complete(self):
        return self.dot >= len(self.tree.children)


class Chart(object):
    def __init__(self):
        self._elements = {}
        self._additions = []
        self.counter = itertools.count()
    def __len__(self):
        return len(self._elements)
    def __iter__(self):
        return iter(self._elements)
    def __getitem__(self, key):
        return self._elements[key]
    def add(self, state, prev = None, reason = None):
        self._additions.append((state, prev, reason))
    def commit(self):
        prev_len = len(self._elements)
        for s, prev, reason in self._additions:
            if s not in self._elements:
                s.index = self.counter.next()
                self._elements[s] = {(prev, reason)}
            else:
                if isinstance(prev, State) and s == prev:
                    continue
                self._elements[s].add((prev, reason))
        del self._additions[:]
        return prev_len != len(self._elements)

def print_chart(chart, completed = False):
    for s in sorted(chart, key = lambda s: s.index):
        if completed and not s.is_complete():
            continue
        reasons = []
        for s2, r in chart[s]:
            if isinstance(s2, tuple):
                reasons.append("(%s,%s):%s" % (s2[0].index, s2[1].index, r))
            else:
                reasons.append("%s:%s" % (getattr(s2, "index", ""), r))
        
        print "% 3d   % -50s    [%s]" % (s.index, s, ", ".join(reasons))


if __name__ == "__main__":
    S = NonTerminal("S")
    NP = NonTerminal("NP")
    VP = NonTerminal("VP")
    V = NonTerminal("V")
    N = NonTerminal("N")
    D = NonTerminal("D")
    Adv = NonTerminal("Adv")
    Adj = NonTerminal("Adj")
    
    g = TIG(
        init_trees = [
            NP("john"),
            NP("mary"),
            N("apple"),
            N("banana"),
            NP(D("a"), N),
            NP(D("an"), N),
            NP(D("the"), N),
            S(NP, VP(V("likes"), NP)),
        ],
        aux_trees = [
            VP(Adv("really"), Foot(VP)),
            N(Adj("tasty"), Foot(N)),
        ],
    )

    def get_paths(s, chart):
        if s is None:
            return
        yield s
        for s2 in get_paths(list(chart[s])[0][0], chart):
            if s2.is_complete():
                yield s2    

    class DerivationTree(object):
        def __init__(self, root, span, children):
            self.root = root
            self.span = span
            self.children = children
        def __str__(self):
            return "%s%s(%s)" % (self.root, self.span, ", ".join(str(c) for c in self.children))
        def show(self, level = 0):
            print "%s%s  %s" % ("    " * level, self.root, self.span)
            for c in self.children:
                if isinstance(c, DerivationTree):
                    c.show(level + 1)
                else:
                    print "    " * (level + 1) + repr(c)
    
    class Span(object):
        def __init__(self, i, j):
            self.i = i
            self.j = j
        def __repr__(self):
            return "[%s..%s]" % (self.i, self.j)
        def inside(self, enclosing):
            return self.i >= enclosing.i and self.j <= enclosing.j
    
    def extract(path):
        trees = []
        while path:
            s = path.pop(0)
            sp = Span(s.i, s.j)
            children = []
            first = None
            last = None
            for i, t in enumerate(trees):
                if t.span.inside(sp):
                    if first is None:
                        first = i
                    last = i
                    children.append(t)
                elif first is not None:
                    break
            
            if children:
                del trees[first:last+1]
                if isinstance(s.tree.children[-1], Foot) and path and path[0].i == s.i:
                    s2 = path.pop(0)
                    sp = Span(s2.i, s2.j)
                    children.append(DerivationTree(s.tree.root, Span(s.j, s2.j), s2.tree.children))
                trees.insert(first, DerivationTree(s.tree.root, sp, children))
            else:
                trees.append(DerivationTree(s.tree.root, sp, s.tree.children))
        
        assert len(trees) == 1
        return trees[0]

    matches, chart = g.parse(S, "john really likes the tasty banana".split())
    path = list(get_paths(matches[0], chart))[::-1]
    print path

    t = extract(path)
    t.show()

    print "================="

    matches, chart = g.parse(NP, "the tasty banana".split())
    path = list(get_paths(matches[0], chart))[::-1]
    print path
    
    t = extract(path)
    t.show()











