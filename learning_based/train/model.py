#coding=utf-8

import numpy as np
import tensorflow as tf

from tensorflow.python.ops import array_ops

class BaseModel():
    """Base model
       Build CNN and loss
    """
    def __init__(self, config_json, training=True):
        self.x_dim, self.y_dim = config_json["screen_res"]
        self.image_channels = config_json["image_channels"]
        self.total_perms = config_json["total_perms"]
        self.word_embedding_dim = config_json["word_embedding_dim"]
        self.focal_loss_gamma = config_json["focal_loss_gamma"]
        self.training = training

        if self.training:
            self.weight_decay = config_json["weight_decay"]
            self.batch_size = config_json["batch_size"]
        else:
            self.weight_decay = 0.0
            self.batch_size = 1

        self.regularizer = tf.contrib.layers.l2_regularizer(scale=self.weight_decay)

        self.input_images = tf.placeholder(dtype=tf.float32,
                                           shape=(None, self.x_dim, self.y_dim, self.image_channels))
        self.input_ui_text = tf.placeholder(dtype=tf.float32,
                                            shape=(None, self.word_embedding_dim))
        self.input_ui_resource_id = tf.placeholder(dtype=tf.float32,
                                                   shape=(None, self.word_embedding_dim))
        self.input_elem_text = tf.placeholder(dtype=tf.float32,
                                              shape=(None, self.word_embedding_dim))
        self.input_elem_resource_id = tf.placeholder(dtype=tf.float32,
                                                     shape=(None, self.word_embedding_dim))
        self.true_perms = tf.placeholder(dtype=tf.float32,
                                         shape=(None, self.total_perms))

        # assign later
        self.image_out = None
        self.ui_text_out = None
        self.ui_resource_id_out = None
        self.elem_text_out = None
        self.elem_resource_id_out = None

    def get_feed_dict(self,
                      images,
                      ui_text, ui_resource_id, elem_text, elem_resource_id,
                      perms):
        return {
            self.input_images: images,
            self.input_ui_text: ui_text,
            self.input_ui_resource_id: ui_resource_id,
            self.input_elem_text: elem_text,
            self.input_elem_resource_id: elem_resource_id,
            self.true_perms: perms
        }

    def build_cnn(self):
        # Do normalize first
        self.normalized_images = tf.subtract(self.input_images, 0.5)
        # 180x320
        self.conv1 = tf.layers.conv2d(inputs=self.normalized_images,
                                      filters=16,
                                      kernel_size=3,
                                      padding="same",
                                      activation=tf.nn.relu,
                                      kernel_regularizer=self.regularizer,
                                      bias_regularizer=self.regularizer,
                                      name="conv1")
        self.pool1 = tf.layers.max_pooling2d(inputs=self.conv1,
                                             pool_size=2,
                                             strides=2,
                                             name="pool1")
        # 90x160
        self.conv2 = tf.layers.conv2d(inputs=self.pool1,
                                      filters=32,
                                      kernel_size=3,
                                      padding="same",
                                      activation=tf.nn.relu,
                                      kernel_regularizer=self.regularizer,
                                      bias_regularizer=self.regularizer,
                                      name="conv2")
        self.pool2 = tf.layers.max_pooling2d(inputs=self.conv2,
                                             pool_size=2,
                                             strides=2,
                                             name="pool2")
        # 45x80
        self.conv3 = tf.layers.conv2d(inputs=self.pool2,
                                      filters=64,
                                      kernel_size=3,
                                      padding="same",
                                      activation=tf.nn.relu,
                                      kernel_regularizer=self.regularizer,
                                      bias_regularizer=self.regularizer,
                                      name="conv3")
        self.pool3 = tf.layers.max_pooling2d(inputs=self.conv3,
                                             pool_size=2,
                                             strides=2,
                                             padding="same",
                                             name="pool3")
        # 23x40
        self.conv4 = tf.layers.conv2d(inputs=self.pool3,
                                      filters=64,
                                      kernel_size=3,
                                      padding="same",
                                      activation=tf.nn.relu,
                                      kernel_regularizer=self.regularizer,
                                      bias_regularizer=self.regularizer,
                                      name="conv4")
        self.pool4 = tf.layers.max_pooling2d(inputs=self.conv4,
                                             pool_size=2,
                                             strides=2,
                                             padding="same",
                                             name="pool4")
        # 12x20
        self.conv5 = tf.layers.conv2d(inputs=self.pool4,
                                      filters=64,
                                      kernel_size=3,
                                      padding="same",
                                      activation=tf.nn.relu,
                                      kernel_regularizer=self.regularizer,
                                      bias_regularizer=self.regularizer,
                                      name="conv5")
        self.pool5 = tf.layers.max_pooling2d(inputs=self.conv5,
                                             pool_size=2,
                                             strides=2,
                                             padding="same",
                                             name="pool5")
        # 6x10

    def build_loss(self):
        self.image_out_flat = tf.reshape(self.image_out,
                                         [-1, 6 * 10 * 64])
        self.ui_text_out_flat = tf.reshape(self.ui_text_out,
                                           [-1, self.word_embedding_dim])
        self.ui_resource_id_out_flat = tf.reshape(self.ui_resource_id_out,
                                                  [-1, self.word_embedding_dim])
        self.elem_text_out_flat = tf.reshape(self.elem_text_out,
                                             [-1, self.word_embedding_dim])
        self.elem_resource_id_out_flat = tf.reshape(self.elem_resource_id_out,
                                                    [-1, self.word_embedding_dim])

        self.combined_out = tf.concat([self.image_out_flat,
                                       self.ui_text_out_flat,
                                       self.ui_resource_id_out_flat,
                                       self.elem_text_out_flat,
                                       self.elem_resource_id_out_flat], axis=1)

        self.fc = tf.layers.dense(self.combined_out,
                                  self.total_perms,
                                  activation=tf.nn.sigmoid,
                                  kernel_regularizer=self.regularizer,
                                  bias_regularizer=self.regularizer,
                                  name="fc")
        # use focal loss from Kaiming He
        self.pt = self.true_perms * self.fc + (1 - self.true_perms) * (1 - self.fc)
        self.perm_loss = -tf.reduce_mean(((1 - self.pt) ** self.focal_loss_gamma) * tf.log(self.pt))
        tf.losses.add_loss(self.perm_loss)

        # total loss
        self.total_loss = tf.losses.get_total_loss()

class SingleScreenModel(BaseModel):
    """Model for processing single screenshot
       Use conv-pool-de-conv for heatmap
       Use conv-pool-fc for predicting

       input: batch_num, x_dim, y_dim, channels
    """
    def __init__(self, config_json):
        super().__init__(config_json)
        self.build_cnn()
        self.build_model()
        self.build_loss()
        if self.training:
            self.build_summary()

    def build_model(self):
        self.image_out = self.pool5
        self.ui_text_out = self.input_ui_text
        self.ui_resource_id_out = self.input_ui_resource_id
        self.elem_text_out = self.input_elem_text
        self.elem_resource_id_out = self.input_elem_resource_id

    def build_summary(self):
        # summary
        tf.summary.scalar("perm_loss", self.perm_loss)
        tf.summary.scalar("total_loss", self.total_loss)
        tf.summary.image("input_images",
                         self.input_images,
                         max_outputs=self.batch_size)
        tf.summary.histogram("normalized_images", self.normalized_images)
        tf.summary.histogram("true_perms", self.true_perms)
        tf.summary.histogram("fc", self.fc)

        tf.summary.histogram("conv1_activation", self.conv1)
        tf.summary.histogram("conv2_activation", self.conv2)
        tf.summary.histogram("conv3_activation", self.conv3)
        tf.summary.histogram("conv4_activation", self.conv4)
        tf.summary.histogram("conv5_activation", self.conv5)
        tf.summary.histogram("conv1_gradient", tf.gradients(self.total_loss, self.conv1))
        tf.summary.histogram("conv2_gradient", tf.gradients(self.total_loss, self.conv2))
        tf.summary.histogram("conv3_gradient", tf.gradients(self.total_loss, self.conv3))
        tf.summary.histogram("conv4_gradient", tf.gradients(self.total_loss, self.conv4))
        tf.summary.histogram("conv5_gradient", tf.gradients(self.total_loss, self.conv5))

