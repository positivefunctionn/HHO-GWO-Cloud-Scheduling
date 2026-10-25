"""Optimizer sanity check; no claim of a research result."""
import random
def sphere(x): return sum(v*v for v in x)
def random_sphere(seed=7, samples=1000):
    r=random.Random(seed); best=min(sphere([r.uniform(-5,5) for _ in range(4)]) for _ in range(samples)); return {"benchmark":"sphere","known_optimum":0.0,"random_reference_best":best}
if __name__=='__main__': print(random_sphere())
