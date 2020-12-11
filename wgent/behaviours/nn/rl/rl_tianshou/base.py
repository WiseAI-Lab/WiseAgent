from wgent.behaviours import RLBehaviour
from tianshou.data.collector import Collector
from tianshou.trainer import offpolicy, onpolicy


class ActorBehaviour(RLBehaviour):
    """
        Get the Data from enviroment use the policy.
    """
    def __init__(self, agent, policy):
        self.agent = agent
        self.policy = policy
        args = self.agent.args
        envs = agent.envs
        # buffer
        self.buffer_size = args.buffer_size
        self.ignore_obs_next = True
        self.save_only_last_obs = True
        self.stack_num = args.frames_stack
        # rl
        self.action_noise = None
        self.sample_avail = False

    def execute(self):
        return self.agent.actor.collect()
    

    def on_start(self):
        buffer = ReplayBuffer(
            size=self.buffer_size, 
            ignore_obs_next=self.ignore_obs_next,
            save_only_last_obs=self.save_only_last_obs, 
            stack_num=self.frames_stack
            sample_avail=self.sample_avail
        )
        self.agent.actor = Collector(
            policy=self.policy,
            env=self.envs,
            buffer=buffer,
            preprocess_fn: self.preprocess_fn,
            action_noise: self.action_noise,
            reward_metric: self.reward_metric,
        )


    def preprocess_fn():
        """
            Define the preprocess_fn here for collector's buffer
        """


    def reward_metric():
        """
            Define the reward_metric here for collector's buffer
        """


class LearnerBehaviour(RLBehaviour):
    """

    """
    def __init__(self, agent, net):
        self.agent = agent
        self.net = net
        self.policy = None
        self.trainer = None
        self.train_collector = self.agent.collector
        self.test_collector = self.agent.collector
        # args
        self.args = self.agent.args
        self.max_epoch: args.epoch
        self.step_per_epoch: args.step_per_epoch
        self.collect_per_step: args.collect_per_step
        self.episode_per_test: args.test_num
        self.batch_size: args.batch_size
        # process value
        self.update_per_step = 1
        self.log_interval = 1
        self.verbose = True
        self.test_in_train = False
        self.cur_epoch = 0
        self.global_step = 0
        self.best_epoch = -1
        self.best_reward = -1.0
        self.stat = {}
        self.start_time = None

        # fn
        self.train_fn = if self._train_fn() else None
        self.test_fn = if self._test_fn() else None
        self.stop_fn = if self._stop_fn() else None
        self.save_fn = if self._save_fn() else None
        self.writer = if self._writer() else None

    def execute(self):
        return self.learn()
    

    def on_start(self):
        """
            Initial behaviour
        """
        self.policy = None
        self.test_in_train = self.test_in_train and self.train_collector.policy == self.policy
        self.agent.learner = self
        self.start_time = time.time()


    def learn():
        args = self.args
        if self.cur_epoch > self.max_epoch:
            return 
        
        # train
        self.policy.train()
        if self.train_fn:
            self.train_fn(self.epoch)
        with tqdm.tqdm(
            total=self.step_per_epoch, desc=f"Epoch #{self.epoch}", **tqdm_config
        ) as t:
            while t.n < t.total:
                result = train_collector.collect(n_episode=self.collect_per_step)
                data = {}
                if test_in_train and stop_fn and stop_fn(result["rew"]):
                    test_result = test_episode(
                        self.policy, self.test_collector, self.test_fn,
                        self.epoch, self.episode_per_test, self.writer, self.global_step)
                    if stop_fn(test_result["rew"]):
                        if self.save_fn:
                            self.save_fn(policy)
                        for k in result.keys():
                            data[k] = f"{result[k]:.2f}"
                        t.set_postfix(**data)
                        return gather_info(
                            self.start_time, self.train_collector, self.test_collector,
                            test_result["rew"])
                    else:
                        self.policy.train()
                        if train_fn:
                            self.train_fn(epoch)
                losses = self.policy.update(
                    0, train_collector.buffer,
                    batch_size=self.batch_size, repeat=self.repeat_per_collect)
                self.train_collector.reset_buffer()
                step = 1
                for v in losses.values():
                    if isinstance(v, list):
                        step = max(step, len(v))
                self.global_step += step * self.collect_per_step
                for k in result.keys():
                    data[k] = f"{result[k]:.2f}"
                    if self.writer and self.global_step % log_interval == 0:
                        self.writer.add_scalar(
                            "train/" + k, result[k], global_step=self.global_step)
                for k in losses.keys():
                    if self.stat.get(k) is None:
                        self.stat[k] = MovAvg()
                    self.stat[k].add(losses[k])
                    data[k] = f"{stat[k].get():.6f}"
                    if self.writer and self.global_step % self.log_interval == 0:
                        self.writer.add_scalar(
                            k, self.stat[k].get(), global_step=self.global_step)
                t.update(step)
                t.set_postfix(**data)
            if t.n <= t.total:
                t.update()
        # test
        result = self.test_episode(self.policy, self.test_collector, self.test_fn, self.epoch,
                            self.episode_per_test, self.writer, self.global_step)
        if self.best_epoch == -1 or self.best_reward < result["rew"]:
            self.best_reward = result["rew"]
            self.best_epoch = epoch
            if self.save_fn:
                self.save_fn(policy)
        if self.verbose:
            print(f"Epoch #{self.epoch}: test_reward: {result['rew']:.6f}, "
                f"best_reward: {self.best_reward:.6f} in #{self.best_epoch}")
        if self.stop_fn and self.stop_fn(best_reward):
            break
        return gather_info(
            start_time, train_collector, test_collector, best_reward)
    

    def _train_fn():
        return None


    def _test_fn():
        return None


    def _stop_fn():
        return None


    def _save_fn():
        return None


    def _writer():
        return None

