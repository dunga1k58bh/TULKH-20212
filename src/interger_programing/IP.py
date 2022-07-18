import time
import numpy as np
from ortools.linear_solver import pywraplp


def main():
    data = create_data_model('../../res/testcase4/test1.txt')
    # Runtime limit is 30 minutes
    solve(data, 30)

def create_data_model(path):
    #Store the data model of the problem
    data = {}
    with open (path, "r") as f:
        lines = f.readlines()
        line = list(map(int,lines[0].strip().split()))
        N = line[0]
        M = line[1]
        SIGMA = N + M
        K = line[2]
        p = np.zeros(2*SIGMA +1, dtype='int')
        q = np.zeros(2*SIGMA +1, dtype='int')
        Q = np.zeros(K+1, dtype='int')
        d = np.zeros((2*SIGMA +1, 2*SIGMA+1), dtype='int')

        line = list(map(int,lines[1].strip().split()))
        for m in range(1,2*SIGMA +1):
            if (m<=N):
                p[m] = 1
            elif (m> SIGMA and m <= SIGMA + N):
                p[m] = -1
            if (m > N and m <= SIGMA):
                q[m] = line[m-N-1]
            elif (m>SIGMA+N and m <=2*SIGMA):
                q[m] = line[m-SIGMA-N-1]*(-1)
            else :
                q[m] = 0
                

        line = list(map(int,lines[2].strip().split()))
        for k in range(1,K+1):
            Q[k] = line[k-1]

        for i in range (0, 2*SIGMA+1):
            line = list(map(int,lines[i+3].strip().split()))
            for j in range(0, 2*SIGMA+1):
                d[i][j] = line[j]

        data['N'] = N
        data['M'] = M
        data['q'] = q.tolist()
        data['p'] = p.tolist()
        data['Q'] = Q.tolist()
        data['d'] = d.tolist()
        data['K'] = K
        data['root'] = 0
        data['SIGMA'] = SIGMA
    return data

def solve(data, time_limit_in_seconds):
    solver = pywraplp.Solver.CreateSolver('SCIP')

    N = data['N']
    M = data['M']
    SIGMA = data['SIGMA']
    K = data['K']
    p = data['p']
    q = data['q']

    ############################## VARIABLES #######################################
    x = {}
    w = {}
    r = {}
    u = {}
    for k in range(1, K +1):
        for i in range(2 * SIGMA + 1):
            for j in range(2 * SIGMA + 1):
                x[k,i,j] = solver.IntVar(0,1,f'x[{k},{i},{j}]')
            w[k,i] = solver.IntVar(max(0, data['q'][i]), min(data['Q'][k], data['Q'][k] + data['q'][i]), f'w[{k},{i}]')
            r[k,i] = solver.IntVar(max(0, data['p'][i]), min(1           , 1            + data['p'][i]), f'r[{k},{i}]')

            u[k,i] = solver.IntVar(0, 2*SIGMA, f'u[{k},{i}]')

    target = solver.IntVar(0, solver.infinity(), 'target')

    ############################## CONSTRAINTS #######################################

    # Tong so canh cua do thi la 2M + 2N + K
    cons1 = solver.Constraint(2* SIGMA + K, 2*SIGMA +K)
    for k in range(1, K+1):
        for i in range(2*SIGMA +1):
            for j in range(2*SIGMA +1):
                cons1.SetCoefficient(x[k,i,j], 1)

    #MTZ
    for k in range(1, K+1):
        for i in range(1, 2*SIGMA+1):
            for j in range(0, 2*SIGMA+1):
                    if j != i:
                        solver.Add(u[k, j] - u[k, i] >= 1 - (2*SIGMA + 1)*(1 - x[k, i, j]))
                        if j == i + SIGMA:
                            solver.Add(u[k, j] >= u[k, i])

    # Moi xe deu xuat phat tu root va ket thuc tai root
    for k in range(1, K+1):
        cons2 = solver.Constraint(1,1)
        cons3 = solver.Constraint(1,1)
        for i in range(1,2*SIGMA +1):
            cons2.SetCoefficient(x[k,data['root'],i],1)
            cons3.SetCoefficient(x[k,i,data['root']],1)

    #Cac dinh khong the di tham chinh no
    for k in range(1, K+1):
        for i in range(2*SIGMA +1):
            solver.Add(x[k, i, i] == 0)


    # Moi dinh khac root deu chi duoc tham 1 lan
    for i in range(1, 2 * SIGMA +1):
        solver.Add(1 == sum(x[k, j, i] for k in range(1, K + 1 ) for j in range(2*SIGMA + 1)))
        solver.Add(1 == sum(x[k, i, j] for k in range(1, K + 1 ) for j in range(2*SIGMA + 1)))

    #Xe di vao diem i thi ra tai diem i
    for k in range(1, K+1):
        for i in range(2*SIGMA +1):
            solver.Add(sum(x[k,j,i] for j in range(2*SIGMA +1)) == sum (x[k,i,j] for j in range(2*SIGMA +1)))

    # # #Don tra 1 doi tuong phai cung tai 1 xe
    for k in range(1, K +1):
        for j in range(1, SIGMA+1):
            solver.Add(sum(x[k, i, j] for i in range(2*SIGMA + 1))
                    == sum(x[k, i, j + SIGMA] for i in range(2*SIGMA +1)))

    # #Tong so nguoi tren xe tai 1 thoi diem
    for k in range(1, K +1):
        solver.Add(r[k, 0] == 0)
        for i in range(2*SIGMA +1):
            for j in range(2*SIGMA +1):
                solver.Add(r[k, j] >= r[k, i] + p[j] - 1000000 * (1 - x[k, i, j]))

    # # # #Tong so hang tai mot thoi diem
    for k in range(1, K +1):
        solver.Add(w[k, 0] == 0)
        for i in range(2*SIGMA +1):
            for j in range(2*SIGMA +1):
                solver.Add(w[k, j] >= w[k, i] + q[j] - 1000000 * (1 - x[k, i, j]))

    objects_term = []
    for k in range(1, K + 1):
        total_distance = sum(x[k, i, j] * data['d'][i][j] for i in range(2*SIGMA + 1) for j in range(2*SIGMA +1))
        objects_term.append(total_distance)

    for object in objects_term:
        solver.Add(object <= target)

    # Set time limit (mili second)
    solver.set_time_limit(1000 * time_limit_in_seconds)

    solver.Minimize(target)
    rt = time.time()
    status = solver.Solve()
    st = time.time()
    print(f'Time running: {st - rt}')

    ############################## PRINT SOLUTION #######################################
    if status == pywraplp.Solver.FEASIBLE or status == pywraplp.Solver.OPTIMAL :
        print(f'Minimal of Maximum distance travel of {K} car = {solver.Objective().Value()}')
        s=0
        count = 0
        for k in range(1, K+1):
            for i in range(2*SIGMA +1):
                for j in range(2*SIGMA +1):
                    if x[k, i, j].solution_value() == 1:
                        count+=1
            path = ['0']
            current = 0
            for i in range(2*SIGMA +1):
                if x[k, 0, i].solution_value() == 1:
                    current = i
                    break;

            path.append(str(current))
            while (current):
                for i in range(2*SIGMA +1):
                    if x[k, current, i].solution_value() == 1:
                        path.append(str(i))
                        current = i
                        break;
            s= '-'.join(path)
            print(f'Xe {k}: {s}')
        print(f'Tong so canh: {count}')

main()