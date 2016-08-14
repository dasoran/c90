#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Sample script of recurrent neural network language model
    for generating text

    This code is ported from following implementation.
    https://github.com/longjie/chainer-char-rnn/blob/master/sample.py

    """
import argparse
import sys

import numpy as np
import six
import six.moves.cPickle as pickle

from chainer import cuda
import chainer.functions as F
import chainer.links as L
from chainer import serializers
from chainer.variable import Variable

import net

parser = argparse.ArgumentParser()
parser.add_argument('--model', '-m', type=str, required=True,
                    help='model data, saved by train_ptb.py')
parser.add_argument('--vocabulary', '-v', type=str, required=True,
                    help='vocabulary data, saved by train_ptb.py')
parser.add_argument('--primetext', '-p', type=str, required=True, default='',
                    help='base text data, used for text generation')
parser.add_argument('--seed', '-s', type=int, default=123,
                    help='random seeds for text generation')
parser.add_argument('--unit', '-u', type=int, default=650,
                    help='number of units')
parser.add_argument('--sample', type=int, default=1,
                    help='negative value indicates NOT use random choice')
parser.add_argument('--length', type=int, default=20,
                    help='length of the generated text')
parser.add_argument('--gpu', type=int, default=-1,
                    help='GPU ID (negative value indicates CPU)')
args = parser.parse_args()

if args.seed != -1:
    np.random.seed(args.seed)

xp = cuda.cupy if args.gpu >= 0 else np

# load vocabulary
with open(args.vocabulary, 'rb') as f:
    vocab = pickle.load(f)
ivocab = {}
for c, i in vocab.items():
    ivocab[i] = c

# should be same as n_units , described in train_ptb.py
n_units = args.unit

lm = net.RNNLM(len(vocab), n_units, train=False)
model = L.Classifier(lm)

serializers.load_npz(args.model, model)

if args.gpu >= 0:
    cuda.get_device(args.gpu).use()
    model.to_gpu()

model.predictor.reset_state()

primetext = args.primetext
if isinstance(primetext, six.binary_type):
    primetext = primetext.decode('utf-8')

if primetext[0] in vocab:
    prev_word = Variable(xp.array([vocab[primetext[0]]], xp.int32))
    sys.stdout.write(primetext[0])
    primetext = primetext[1:]
else:
    print('ERROR: Unfortunately ' + primetext + ' is unknown.')
    exit()

prob = F.softmax(model.predictor(prev_word))

#for i in six.moves.range(args.length):
while(True):
    prob = F.softmax(model.predictor(prev_word))
    if args.sample > 0:
        probability = cuda.to_cpu(prob.data)[0].astype(np.float64)
        probability /= np.sum(probability)
        index = np.random.choice(range(len(probability)), p=probability)
    else:
        index = np.argmax(cuda.to_cpu(prob.data))

    if len(primetext) == 0:
        prev_word = Variable(xp.array([index], dtype=xp.int32))
        if ivocab[index] == '<eos>':
            sys.stdout.write('.')
        elif ivocab[index] == '。':
            sys.stdout.write(ivocab[index])
            break
        else:
            sys.stdout.write(ivocab[index])
    else:
        prev_word = Variable(xp.array([vocab[primetext[0]]], xp.int32))
        sys.stdout.write(primetext[0])
        primetext = primetext[1:]

sys.stdout.write('\n')
