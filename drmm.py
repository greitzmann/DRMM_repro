import tensorflow as tf


class DRMM():

    def __init__(self, num_layers, units, activation_functions, max_query_len, num_bins, emb_size, gating_function,
                 seed, learning_rate):
        self.gating_function = gating_function
        self.max_query_len = max_query_len
        self.matching_histograms = tf.placeholder(dtype=tf.float32, shape=(None, max_query_len, num_bins))
        self.queries_idf = tf.placeholder(dtype=tf.float32, shape=(None, max_query_len))
        self.queries_embeddings = tf.placeholder(dtype=tf.float32, shape=(None, max_query_len, emb_size))
        self.num_layers = num_layers
        self.SEED = seed
        self.layers = []
        for i in range(self.num_layers):
            self.layers.append(tf.layers.Dense(units=units[i], activation=activation_functions[i],
                                               kernel_initializer=tf.glorot_uniform_initializer(seed=self.SEED)))
        self.sims = self.compute_scores()
        self.loss = tf.reduce_mean(tf.maximum(0.0, 1 - self.sims[::2] + self.sims[1::2]))
        self.optimizer = tf.train.AdagradOptimizer(learning_rate).minimize(self.loss, name="train_opt")
        # self.optimizer = tf.train.AdamOptimizer().minimize(self.loss, name="train_opt")

    def compute_scores(self):
        hist_hidden_repr = self.compute_hist_hidden_repr(self.matching_histograms)
        hist_hidden_repr = tf.reshape(hist_hidden_repr, shape=(-1, self.max_query_len))
        if self.gating_function == "idf":
            out_gate = self.compute_term_gating_idf(hist_hidden_repr)
        elif self.gating_function == "emb":
            out_gate = self.compute_term_gating_emb(hist_hidden_repr)
        last_op = tf.reduce_sum(out_gate, axis=-1)  # sum last dimension
        return last_op

    def compute_hist_hidden_repr(self, inputs):
        out = self.layers[0](inputs)
        for i in range(1, self.num_layers):
            out = self.layers[i](out)
        return out

    def compute_term_gating_idf(self, hist_hidden_repr):
        queries_idf_hidden_repr = tf.layers.Dense(units=1, activation="softmax",
                                                  kernel_initializer=tf.glorot_uniform_initializer(seed=self.SEED))(self.queries_idf)
        return tf.multiply(queries_idf_hidden_repr, hist_hidden_repr)

    def compute_term_gating_emb(self, hist_hidden_repr):
        queries_emb_hidden_repr = tf.layers.Dense(units=1, activation="softmax",
                                                  kernel_initializer=tf.glorot_uniform_initializer(seed=self.SEED))(self.queries_embeddings)
        queries_emb_hidden_repr = tf.squeeze(queries_emb_hidden_repr)
        return tf.multiply(queries_emb_hidden_repr, hist_hidden_repr)
