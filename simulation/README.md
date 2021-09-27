# Simulation

**Evaluator**

The files related to evaluating traces, this includes the different implementations for our proposed strategies, the baseline LRU strategy, and Belady's MIN.

**Generator**

The files related to generating the traces.  This includes both the Zipf generator and Page Map generator.   The random generator can be simulated by changing the way resources are picked in the Zipf generator to a uniform selection instead in the `__pick_resources` function.
