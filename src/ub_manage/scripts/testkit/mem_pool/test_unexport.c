#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/mman.h>
#include <unistd.h>
#include <time.h>
#include <libobmm.h>
#include <errno.h>

int main(int argc, char *argv[])
{
	unsigned long mem_id;
	clock_t start_time, end_time;
	double execution_time;

	if (argc != 2) {
		printf("Invalid input");
		return 1;
	}

	char *endptr;
	mem_id = strtoul(argv[1], &endptr, 10);

	start_time = clock();
	int res = obmm_unexport(mem_id, 0);
	end_time = clock();
	execution_time = (double)(end_time - start_time) / CLOCKS_PER_SEC;
	printf("obmm_unexport execute time=%.6fs \n", execution_time);

	if (res == 0) {
		printf("mem_id %lu unexport SUCCESS.\n", mem_id);
		return 0;
	} else {
		printf("mem_id %lu unexport FAILED: errno=%d\n", mem_id, errno);
		perror("obmm_unexport");
		return 1;
	}
}
