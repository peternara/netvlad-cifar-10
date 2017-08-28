# -*- coding: utf-8 -*-

import tensorflow as tf

import netvlad
import netvlad_1
import A_softmax
import train_utils
import os
import math



tf.app.flags.DEFINE_string('checkpoint_dir', 'checkpoint', 'directory to save trained models')

tf.app.flags.DEFINE_integer('batch_size', 100, 'num of triplets in a batch')
tf.app.flags.DEFINE_integer('numEpoch', 30, 'num of epochs to train')
tf.app.flags.DEFINE_float('lr', 0.001, 'initial learning rate')
tf.app.flags.DEFINE_integer('print_every', 5, 'print every ... batch')
tf.app.flags.DEFINE_integer('save_every', 5, 'save model every ... epochs')

tf.app.flags.DEFINE_boolean('use_vlad', True, 'use vlad pooling or not')
FLAGS = tf.app.flags.FLAGS


def main(_):
    config = tf.ConfigProto(allow_soft_placement = True)
    with tf.device('/gpu:0'):
        with tf.Session(config = config) as sess:
            X = tf.placeholder(tf.float32, [FLAGS.batch_size, 32, 32, 3], name = 'X')
            Y = tf.placeholder(tf.int64, [FLAGS.batch_size], name = 'Y')
            
            if FLAGS.use_vlad:
                model = netvlad_1.Netvlad()
            else:
                model = netvlad.Netvlad()
            model.build(X)
            print("number of total parameters in the model is %d\n" % model.get_var_count())


            loss, output1, output2 = A_softmax.A_softmax(model.fc2, tf.one_hot(Y, depth = 10), model.fc3, 3)
            # loss = tf.reduce_mean(-tf.log(tf.nn.softmax(model.fc3)) * tf.one_hot(Y, depth = 10))
            train = tf.train.RMSPropOptimizer(FLAGS.lr).minimize(loss)

            output3 = model.fc3

            correct_prediction = tf.equal(tf.argmax(tf.nn.softmax(model.fc3), axis = 1), Y)
            accuracy = tf.reduce_mean(tf.cast(correct_prediction, 'float'))

            sess.run(tf.global_variables_initializer())

            train_loss = 0
            numBatch = 50000 / FLAGS.batch_size

            print("training begins!\n")
            for i in range(FLAGS.numEpoch):
                count = 0.0
                for x, y in train_utils.next_batch(FLAGS.batch_size, 'cifar-10-batches-py'):
                    count += 1
                    _, train_loss, acc, out1, out2, out3 = sess.run([train, loss, accuracy, output1, output2, output3], feed_dict = {X: x, Y: y})
                    # _, train_loss, acc, out3 = sess.run([train, loss, accuracy, output3], feed_dict = {X: x, Y: y})
                    if count % FLAGS.print_every == 0:
                        print("Epoch: %s    progress: %.4f  accuracy = %.4f      training_loss = %.6f\n" % (i, count / numBatch, acc, train_loss))
                        print(out1[:10])
                        print(out2[:10])
                        print(out3[:10, 0])
                if (i + 1) % FLAGS.save_every == 0:
                    model.save_npy(sess, "%s/epoch_%d_loss_%.6f" % (FLAGS.checkpoint_dir, i, train_loss))
                
if __name__ == '__main__':
    tf.app.run()