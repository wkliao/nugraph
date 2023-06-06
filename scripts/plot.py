#!/usr/bin/env python

import sys
import os
import argparse
import pytorch_lightning as pl
import pynuml
import nugraph as ng
import time

Data = ng.data.H5DataModule
Model = ng.models.NuGraph2

def configure():
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('--devices', nargs='+', type=int, default=None,
                        help='List of devices to run inference with')
    parser.add_argument('--checkpoint', type=str, default=None,
                        help='Checkpoint file to resume training from')
    parser.add_argument('--outdir', type=str, required=True,
                        help='Output directory to write plots to')
    parser.add_argument('--limit-predict-batches', type=int, default=10,
                        help='Number of batches to plot')
    parser = Data.add_data_args(parser)
    parser = Model.add_model_args(parser)
    return parser.parse_args()

def plot(args):

    # Load dataset
    nudata = Data(args.data_path,
                  batch_size=args.batch_size,
                  planes=['u','v','y'],
                  classes=['MIP','HIP','shower','michel','diffuse'])

    if args.checkpoint is not None:
        model = Model.load_from_checkpoint(args.checkpoint)
        model.freeze()

        if args.devices is None:
            print('No devices specified – running inference on CPU')

        accelerator = 'cpu' if args.devices is None else 'gpu'
        trainer = pl.Trainer(accelerator=accelerator,
                             devices=args.devices,
                             limit_predict_batches=args.limit_predict_batches,
                             logger=None)

    plot = pynuml.plot.GraphPlot(planes=nudata.planes, classes=nudata.classes)

    if args.checkpoint is None:
        for i, batch in enumerate(nudata.test_dataloader()):
            if args.limit_predict_batches is not None and i >= args.limit_predict_batches:
                break
            for data in batch.to_data_list():
                md = data['metadata']
                name = f'r{md.run.item()}_sr{md.subrun.item()}_evt{md.event.item()}'
                plot.plot(data, name=f'{args.outdir}/{name}_semantic_true', target='semantic', how='true', filter='true')
                plot.plot(data, name=f'{args.outdir}/{name}_filter_true', target='filter', how='true')
    else: 
        for batch in trainer.predict(model, nudata.test_dataloader()):
            for data in batch:
                md = data['metadata']
                name = f'r{md.run.item()}_sr{md.subrun.item()}_evt{md.event.item()}'
                plot.plot(data, name=f'{args.outdir}/{name}_semantic_true', target='semantic', how='true', filter='true')
                plot.plot(data, name=f'{args.outdir}/{name}_semantic_pred', target='semantic', how='pred', filter='true')
                plot.plot(data, name=f'{args.outdir}/{name}_filter_true', target='filter', how='true')
                plot.plot(data, name=f'{args.outdir}/{name}_filter_pred', target='filter', how='pred')

if __name__ == '__main__':
    args = configure()
    plot(args)