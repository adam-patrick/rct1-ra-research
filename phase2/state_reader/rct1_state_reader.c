#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/uio.h>
#include <unistd.h>

static int num(const char*s){if(!s||!*s)return 0;for(;*s;s++)if(*s<'0'||*s>'9')return 0;return 1;}
static int find_pid(void){DIR*d=opendir("/proc");if(!d)return -1;struct dirent*e;while((e=readdir(d))){if(!num(e->d_name))continue;char p[128],n[64]={0};snprintf(p,sizeof p,"/proc/%s/comm",e->d_name);FILE*f=fopen(p,"r");if(!f)continue;int ok=fgets(n,sizeof n,f)!=NULL;fclose(f);n[strcspn(n,"\r\n")]=0;if(ok&&!strcmp(n,"RCT.EXE")){closedir(d);return atoi(e->d_name);}}closedir(d);return -1;}
static uintptr_t base_for(int pid){char p[128],line[1024];snprintf(p,sizeof p,"/proc/%d/maps",pid);FILE*f=fopen(p,"r");if(!f)return 0;uintptr_t a,z,off;char perms[8],path[512];while(fgets(line,sizeof line,f)){path[0]=0;if(sscanf(line,"%"SCNxPTR"-%"SCNxPTR" %7s %"SCNxPTR" %*s %*s %511[^\n]",&a,&z,perms,&off,path)>=4&&strstr(line,"/RCT.EXE")){fclose(f);return a-off;}}fclose(f);return 0;}
int main(void){
 int pid=find_pid();if(pid<0){puts("RCT1 not running");return 2;}uintptr_t base=base_for(pid);if(!base){puts("RCT1 detected, but RCT.EXE mapping was not found");return 3;}
 printf("RCT1 detected\nBuild: RollerCoaster Tycoon Deluxe\nPID: %d\nModule base: 0x%08"PRIxPTR"\n",pid,base);
 /* A nearby integer matched one observed cash display, but it was not
    reproduced after the next simulation tick. Keep this reader conservative
    until a stable locator is validated across launches. */
 puts("Cash: unavailable (candidate not yet validated)");
 puts("Guests: unavailable (locator not yet established)");
 puts("Park Rating: unavailable (locator not yet established)");
 puts("Safety: read-only process_vm_readv; no process write APIs are used.");
 return 0;
}
