'''
Sam Congdon
CSCI 460: Operating Systems
Assignment 3: Priority Inversion
2 December 2017

This python module simulates the processing of three tasks utilizing priority inversion. Tasks 1 and 3 utilize
a shared buffer resource, and thus cannot be preempted by one another. Additionally, they cannot be run until the
buffer is available, which is only released upon task completion, which causes the priority inversion. Task 2 can
be preempted by Task 1, and preempt Task 3. Preempted tasks are stored in a queue, in which they can be forced to
wait for higher priority tasks to be run before they are.
'''


class Buffer:
    ''' This class manages a buffer object used by tasks 1 and 3, containing three numbers
        that are altered by the tasks. '''
    def __init__(self):
        self.locked = False
        self.contents = ['0', '0', '0']

class Task:
    ''' This class manages a Task object, tracking its identity, required time, and state (which is
        either a buffer or a list tracking its steps completed. '''
    def __init__(self, task):
        self.type = task

        # create the subscripted name
        SUB = str.maketrans("123", "₁₂₃")
        self.name = 'T' + str(task).translate(SUB)

        if task == 1:
            self.priority = 3
            self.time = 3
        elif task == 2:
            self.priority = 2
            self.time = 10
        elif task == 3:
            self.priority = 1
            self.time = 3
        self.position = 0
        self.state = ['' for _ in range(self.time)]
        self.completed = False
        self.has_buffer = False

    def update_state(self):
        # updates the tasks state based on its identity
        if self.type == 1:
            self.state[self.position] = '1'
        if self.type == 2:
            self.state[self.position] = 'N'
        if self.type == 3:
            self.state[self.position] = '3'
        self.position += 1
        # check if the task has been completed
        if self.position == self.time:
            self.completed = True

class Job:
    ''' This class manages a Job object, which consists of a task and an arrival time. '''

    def __init__(self, time, task):
        self.time = time
        self.task = Task(task)

class Job_Queue:
    ''' This class is used to track jobs that have arrived but are waiting for another job to finish
        before they can start, as well as storing any jobs that have been preempted. The queue sorts jobs
        by their priority, with the highest priority jobs always leaving first. '''

    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs += [job]
        self.jobs.sort(key=lambda x: x.task.priority, reverse=True)
        #self.jobs.sort(key=(0))


def run_jobs(fout, job_list):
    ''' This method processes a list of jobs allowing for priority inversion to occur. '''

    buffer = Buffer()
    job_queue = Job_Queue()
    current_time = 0
    current_job = 0
    start_time = 0

    # as long as there remains a job to be completed
    while job_list or job_queue.jobs or current_job:

        # if there is no job running
        if not current_job:
            # first check if the queue is empty, if so load the next job from the list
            if not job_queue.jobs:
                current_job = job_list.pop(0)
                # if the job needs to take the buffer, do so
                if current_job.task.type != 2:
                    current_job.task.has_buffer = True
                    buffer.locked = True
                    current_job.task.state = buffer.contents
                current_time = current_job.time
            # then load the next highest priority job that has the buffer, or doesn't need it.
            else:
                # if the buffer is open take the next job in the queue
                if not buffer.locked:
                    current_job = job_queue.jobs.pop(0)
                    # if this job needs the buffer, access it
                    if current_job.task.type != 2:
                        current_job.task.has_buffer = True
                        buffer.locked = True
                        current_job.task.state = buffer.contents
                else:
                    # else take the next job that has the buffer, or doesnt' need it
                    for job in job_queue.jobs:
                        if job.task.type == 2 or job.task.has_buffer:
                            current_job = job
                            job_queue.jobs.remove(job)
                #current_job = job_queue.jobs.pop(0)
            #load the buffers contents if the task uses it
            #if current_job.task.type != 2: current_job.task.state = buffer.contents
            start_time = current_time

        # if a new job just arrived
        elif (job_list and job_list[0].time <= current_time):
            new_job = job_list.pop(0)
            # if the new job can preempt the current job
            if (new_job.task.priority > current_job.task.priority) and (new_job.task.type != 1 or not buffer.locked):
                # output the current jobs state, then store the current job in the queue
                fout.write('time {}, {}{}{}\n'.format(start_time, current_job.task.name, ''.join(current_job.task.state[:current_job.task.position]),
                                                   current_job.task.name))
                job_queue.add_job(current_job)
                # start the new job
                current_job = new_job
                # if the job needs to take the buffer, do so
                if current_job.task.type == 1:
                    current_job.task.has_buffer = True
                    buffer.locked = True
                start_time = current_time
            # else add the new job to the queue
            else:
                job_queue.add_job(new_job)
        # process the current jobs state after another ms has passed
        current_time += 1
        current_job.task.update_state()
        # if the current job has just completed, output it and clear the current job
        if current_job.task.completed:
            fout.write('time {}, {}{}{}\n'.format(start_time, current_job.task.name, ''.join(current_job.task.state),
                                               current_job.task.name))
            # unlock the buffer if the current task had it
            if current_job.task.has_buffer: buffer.locked = False
            current_job = None

    fout.write('\n')

def get_job_list(fout, manual_input = False, supplied = False, random = False, num_jobs = 10):
    ''' This method creates a list of jobs to be run, parameters are used to determine where the
        jobs are intialized from. '''
    job_list = []

    # get a job list from terminal input
    if manual_input:
        job_list = input('Enter job list in the form < 1,3 >,< 3,2 >,< 6,3 >')
        job_list = job_list.replace(' ', '')
        job_list = job_list.replace('>,', '')
        job_list = job_list[1:-1].split('<')
        job_list = [[int(x) for x in job.split(',')] for job in job_list]
        fout.write('Running on input job sequence {}\n'.format(job_list))

    # use the supplied job list
    elif supplied:
        # job_list = '< 1,3 >,< 3,2 >,< 6,3 >,< 8,1 >,< 10,2 >,< 12,3 >,< 26,1 >'
        job_list = [[1,3], [3,2], [6,3], [8,1], [10,2], [12,3], [26,1]]
        fout.write('Running on supplied job sequence {}\n'.format(job_list))

    # randomly generate a job list
    elif random:
        import random
        times = sorted(random.sample(range(30), num_jobs))
        tasks = [random.randint(1, 3) for _ in range(num_jobs)]
        job_list = [[times[i], tasks[i]] for i in range(num_jobs)]
        fout.write('Running on random job sequence {}\n'.format(job_list))

    # return a list of Job objects created from the [time, task] lists
    return [Job(j[0], j[1]) for j in job_list]


def main():
    fout = open('congdon_samuel-3.output', 'w')
    run_jobs(fout, get_job_list(fout, random=True))
    run_jobs(fout, get_job_list(fout, supplied=True))
    fout.close()

if __name__ == '__main__':
    main()
