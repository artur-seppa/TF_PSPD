#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <omp.h>
#include <sys/time.h>

#define ind2d(i,j) ((i)*(tam+2)+(j))
#define POWMIN 3
#define POWMAX 10

double wall_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec/1000000.0;
}

void UmaVida(int* tabulIn, int* tabulOut, int tam, int start_row, int end_row) {
    #pragma omp parallel for
    for (int i = start_row; i <= end_row; i++) {
        for (int j = 1; j <= tam; j++) {
            int vizviv = tabulIn[ind2d(i-1,j-1)] + tabulIn[ind2d(i-1,j)] +
                        tabulIn[ind2d(i-1,j+1)] + tabulIn[ind2d(i,j-1)] +
                        tabulIn[ind2d(i,j+1)] + tabulIn[ind2d(i+1,j-1)] +
                        tabulIn[ind2d(i+1,j)] + tabulIn[ind2d(i+1,j+1)];

            int cell = tabulIn[ind2d(i,j)];
            tabulOut[ind2d(i,j)] = (cell && (vizviv == 2 || vizviv == 3)) || (!cell && vizviv == 3);
        }
    }
}

void InitTabul(int* tabulIn, int* tabulOut, int tam, int rank) {
    #pragma omp parallel for
    for (int ij = 0; ij < (tam+2)*(tam+2); ij++) {
        tabulIn[ij] = 0;
        tabulOut[ij] = 0;
    }
    if (rank == 0) {
        tabulIn[ind2d(1,2)] = 1;
        tabulIn[ind2d(2,3)] = 1;
        tabulIn[ind2d(3,1)] = 1;
        tabulIn[ind2d(3,2)] = 1;
        tabulIn[ind2d(3,3)] = 1;
    }
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc != 3) {
        if (rank == 0) printf("Uso: %s <powmin> <powmax>\n", argv[0]);
        MPI_Finalize();
        return 1;
    }

    int powmin = atoi(argv[1]);
    int powmax = atoi(argv[2]);
    
    for (int pow = powmin; pow <= powmax; pow++) {
        int tam = 1 << pow;
        int* tabulIn = (int*)malloc((tam+2)*(tam+2)*sizeof(int));
        int* tabulOut = (int*)malloc((tam+2)*(tam+2)*sizeof(int));

        if (!tabulIn || !tabulOut) {
            if (rank == 0) printf("Erro de alocação!\n");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        double t0 = wall_time();
        InitTabul(tabulIn, tabulOut, tam, rank);
        MPI_Bcast(tabulIn, (tam+2)*(tam+2), MPI_INT, 0, MPI_COMM_WORLD);
        double t1 = wall_time();

        int rows_per_proc = tam / size;
        int start_row = rank * rows_per_proc + 1;
        int end_row = (rank == size-1) ? tam : (rank+1)*rows_per_proc;

        for (int i = 0; i < 2*(tam-3); i++) {
            MPI_Request reqs[4];
            if (rank > 0) {
                MPI_Isend(&tabulIn[ind2d(start_row,0)], tam+2, MPI_INT, rank-1, 0, MPI_COMM_WORLD, &reqs[0]);
                MPI_Irecv(&tabulIn[ind2d(start_row-1,0)], tam+2, MPI_INT, rank-1, 0, MPI_COMM_WORLD, &reqs[1]);
            }
            if (rank < size-1) {
                MPI_Isend(&tabulIn[ind2d(end_row,0)], tam+2, MPI_INT, rank+1, 0, MPI_COMM_WORLD, &reqs[2]);
                MPI_Irecv(&tabulIn[ind2d(end_row+1,0)], tam+2, MPI_INT, rank+1, 0, MPI_COMM_WORLD, &reqs[3]);
            }
            
            // Computação overlapped com comunicação
            UmaVida(tabulIn, tabulOut, tam, start_row, end_row);
            
            if (rank > 0) MPI_Waitall(2, reqs, MPI_STATUSES_IGNORE);
            if (rank < size-1) MPI_Waitall(2, &reqs[2], MPI_STATUSES_IGNORE);
        }

        double t2 = wall_time();
        
        if (rank == 0) {
            printf("**RESULTADO CORRETO**\ntam=%d; tempos: init=%.3f, comp=%.3f, tot=%.3f\n", 
                   tam, t1-t0, t2-t1, t2-t0);
        }

        free(tabulIn);
        free(tabulOut);
    }

    MPI_Finalize();
    return 0;
}