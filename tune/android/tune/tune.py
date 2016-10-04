# Copyright (c) 2015, PHILIPPE TILLET. All rights reserved.
# 
# This file is part of ISAAC.
# 
# ISAAC is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301  USA


import random, argparse, json, os
from math import log, isinf
from itertools import chain, product
from numpy import argsort, argmax, where, delete, bincount
from operator import mul
import isaac as sc
from tools import profile_execution_failure
from isaac.external.sklearn.forest import RandomForestRegressor
import optimize, tools, model
from json import encoder
import json, csv
import numpy as np


encoder.FLOAT_REPR = lambda o: format(o, '.2f')
encoder.separators = (',',':')

def unique(L):
    seen = set()
    seen_add = seen.add
    return [ x for x in L if not (x in seen or seen_add(x))]

def pow2range(a, b):
    return [2**x for x in range(a, b)]


class Tuner:

    def __init__(self, logger, device, operation, json_path, progress_bar):
        self.logger = logger
        self.device = device
        self.operation = operation
        self.json_path = json_path
        self.progress_bar = progress_bar
        
  
    def run(self, level = 'intermediate'): 
        
        assert level in ['simple', 'intermediate', 'full']
        
        device = self.device
        operation = self.operation
        context = sc.driver.context(device)
        
        if self.logger:
            self.logger.info("----------------")
            self.logger.info(operation.__name__.replace('_','-').upper())
            self.logger.info("----------------")

        #BLAS1 training sizes
        if operation in [sc.templates.elementwise_1d, sc.templates.reduce_1d]:
            sizes = [(x,) for x in tools.expspace(1e3, 1e8, 20)]
        
        #BLAS2 training sizes
        if operation in [sc.templates.elementwise_2d, sc.templates.reduce_2d_rows, sc.templates.reduce_2d_cols]:
            sizes = []
            #Square
            for N in [896, 1760, 2048, 2560]:
                sizes += [(N, N)]
            #Tall and Skinny
            for M in [16, 32, 64, 128]:
                for N in [1024, 4096, 16384, 65536, 262144]:
                    sizes += [(M, N)]
                    sizes += [(N, M)]
        
        #BLAS3 training sizes
        if operation in [sc.templates.gemm_nn, sc.templates.gemm_nt, sc.templates.gemm_tn, sc.templates.gemm_tt]:
            sizes = []
            #Square
            for N in [896, 1760, 2048, 2560]:
                sizes += [(N, N, N)]
            #LaPack
            for N in [896, 1760, 2048, 2560]:
			   for K in [16, 32, 64, 128]:
				   sizes += [(N, N, K)]
            #Covariance
            for N in [16, 32, 64, 128]:
			   for K in [16000,32000,64000,128000]:
				   sizes += [(N, N, K)]
            #DeepSpeech
            for M in [1760, 2048, 2560]:
                for N in [16, 32, 64, 128, M]:
                    sizes += [(M, N, M)]

        #Training data
        performance = tools.metric_of(operation)
        profiles, X, Y = [], [], []
        
        #Restore progress
        savepath = os.path.join('save', operation.__name__)
        if not os.path.exists(savepath):
            os.makedirs(savepath)
        try:
            with open(os.path.join(savepath, 'X.csv')) as f:
                X = [tuple(map(int, row)) for row in csv.reader(f, delimiter=',')]
            with open(os.path.join(savepath, 'Y.csv')) as f:
                Y = [map(float, row) for row in csv.reader(f, delimiter=',')]
            with open(os.path.join(savepath, 'profiles.csv')) as f:
                def mmap(x):
                    if x=='FETCH_FROM_LOCAL':
                        return sc.templates.fetch_type.FETCH_FROM_LOCAL
                    if x=='FETCH_FROM_GLOBAL_CONTIGUOUS':
                        return sc.templates.fetch_type.FETCH_FROM_GLOBAL_CONTIGUOUS
                    if x=='FETCH_FROM_GLOBAL_STRIDED':
                        return sc.templates.fetch_type.FETCH_FROM_GLOBAL_STRIDED
                    return int(x)
                profiles = [map(mmap,row) for v in row for row in csv.reader(f, delimiter=',')]
        except:
            pass
        
        #Tuning
        for idx, x in enumerate(sizes):
            #Create new line on log
            if idx>0:
             self.progress_bar.set_finished()
            self.progress_bar.set_prefix(', '.join(map(str, x)))
            #Skip if already saved
            if x in X:
                row = Y[X.index(x)]
                self.progress_bar.update(1, 1, profiles[argmax(row)], max(row))
                continue
            tree, operands = tools.tree_of(operation, x, context)
            #Check if GA needs to run (i.e., current best prediction is not a local optimum)
            tune = True
            best = None
            if idx > 0:
                dim = min(10, idx+1)
                clf = RandomForestRegressor(dim, dim).fit(X, Y)
                predictions = clf.predict(x)[0]
                for idx in (-predictions).argsort():
                    ts = tools.benchmark(operation(*profiles[idx]), tree)
                    if np.isfinite(ts):
                        break
                if np.isfinite(ts):
                    best = profiles[idx]
                    tune = not optimize.is_local_optimum(predicted, operation, x, context)
            #Retune if necessary
            if tune:
                optimizer = optimize.GeneticOptimizer(self.logger, naccept=1000, niter=1000, cxpb=.4, mutpb=.4, popsize=20, progress_bar = self.progress_bar)
                best = optimizer.run(operation, x, context, prior=best)[0]
                if best not in profiles:
                    profiles.append(best)
                    for xx,yy in zip(X, Y):
                        tree, _operands = tools.tree_of(operation, xx, context)
                        time = tools.benchmark(operation(*best), _tree)
                        yy.append(performance(xx, time))
            #Update dataset
            X.append(x)
            y = [performance(x,tools.benchmark(operation(*prf), tree)) for prf in profiles]
            Y.append(y)
            #Save data
            for (fname, data) in zip(['X.csv', 'Y.csv', 'profiles.csv'], [X, Y, profiles]):
                with open(os.path.join(savepath, fname), 'wb') as f:
                    csv.writer(f).writerows(data)
            #print performance info in case no tuning was done
            if not tune:
                row = Y[X.index(x)]
                self.progress_bar.update(1, 1, profiles[argmax(row)], max(row))
        self.progress_bar.set_finished()
        
        #Adding external profiles
        for prof in tools.external_profiles(operation):
			for x, y in zip(X, Y):
				tree, operands = tools.tree_of(operation, x, context)
				perf = performance(x,tools.benchmark(prof, tree))
				if perf > 0:
					profiles.append(prof.__class__.__name__)
					y.append(perf)
            
        #Pruning of useless profiles
        if len(Y[0]) > 1:
            unused = np.where(np.bincount(np.argmax(Y, 1))==0)[0]
            profiles = [p for ip,p in enumerate(profiles) if ip not in unused]
            Y = np.delete(Y, np.where(np.bincount(np.argmax(Y, 1))==0), axis=1).tolist()          
        
        #Exporting to JSON
        json_path = tools.sanitize(device.name) + '.json' if not self.json_path else self.json_path
        if os.path.isfile(json_path):
            json_data = json.load(open(json_path, 'r'))
        else:
            json_data = {}
            json_data["version"] = "1.0"
        operation_name = operation.__name__
        if operation_name not in json_data:
            json_data[operation_name] = {}
        json_data[operation_name]['float32'] = {}
        D = json_data[operation_name]['float32']
        if len(profiles) > 1:
            clf, nrmse = model.train(X, Y, profiles)
            D['predictor'] = [{'children_left': e.tree_.children_left.tolist(),
                                'children_right': e.tree_.children_right.tolist(),
                                'threshold': e.tree_.threshold.astype('float64').tolist(),
                                'feature': e.tree_.feature.astype('float64').tolist(),
                                'value': e.tree_.value[:,:,0].astype('float64').tolist()} for e in clf.estimators_]
        D['profiles'] = [map(int, x) for x in profiles]
        json.dump(json_data, open(json_path,'w'))
