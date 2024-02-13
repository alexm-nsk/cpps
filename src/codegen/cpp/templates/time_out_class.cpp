// used for time-limiting a function's execution
class $class_name{

  private:
    pthread_mutex_t calculating = PTHREAD_MUTEX_INITIALIZER;
    pthread_cond_t done = PTHREAD_COND_INITIALIZER;
    pthread_t tid;

  static void *callback(void *args){
    $class_name *f = ($class_name *)args;
    $write_retvals
    pthread_cond_signal(&f->done);
    return NULL;
  }
  public:
    $args
    $declare_retvals

  $class_name($call_args, int time){

    struct timespec max_wait;
    struct timespec abs_time;
    int err;
    $copy_args

    memset(&max_wait, 0, sizeof(max_wait));
    max_wait.tv_sec = time;
    clock_gettime(CLOCK_REALTIME, &abs_time);
    abs_time.tv_sec += max_wait.tv_sec;
    abs_time.tv_nsec += max_wait.tv_nsec;
    pthread_mutex_lock(&calculating);
    pthread_create(&tid, NULL, callback, this);
    err = pthread_cond_timedwait(&done, &calculating, &abs_time);
    if (err == ETIMEDOUT){
      $set_error_value
      //fprintf(stderr, "%s: calculation timed out\n", __func__);
    }
    if (!err)
      pthread_mutex_unlock(&calculating);
  }
};
