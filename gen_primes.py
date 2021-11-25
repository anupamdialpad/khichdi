def sieve(no):
    no += 1
    prime = [True] * no
    for i in range(2, no):
        if prime[i]:
            yield i
            for j in range(i, no, i):
                prime[j] = False

primes = list(no for no in sieve(100))
print(*primes, sep='\n')
