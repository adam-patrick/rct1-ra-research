#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/uio.h>
#include <unistd.h>

static int np(const char *s){if(!s||!*s)return 0;for(;*s;s++)if(*s<'0'||*s>'9')return 0;return 1;}
static int pid_rct(void){DIR*d=opendir("/proc");if(!d)return -1;struct dirent*e;while((e=readdir(d))){if(!np(e->d_name))continue;char p[128],n[64]={0};snprintf(p,sizeof p,"/proc/%s/comm",e->d_name);FILE*f=fopen(p,"r");if(!f)continue;int found=fgets(n,sizeof n,f)!=NULL;n[strcspn(n,"\r\n")]=0;fclose(f);if(found&&!strcmp(n,"RCT.EXE")){closedir(d);return atoi(e->d_name);}}closedir(d);return -1;}
static int match(uint8_t *b,size_t i,uint32_t v,int w){if(w==2)return b[i]==(v&255)&&b[i+1]==((v>>8)&255);return b[i]==(v&255)&&b[i+1]==((v>>8)&255)&&b[i+2]==((v>>16)&255)&&b[i+3]==((v>>24)&255);}
int main(int ac,char**av){
 int pid=pid_rct(); if(pid<0){puts("RCT1 not running");return 2;}
 if(ac<2){fprintf(stderr,"usage: %s value [value...]\n",av[0]);return 2;}
 uint32_t vals[32];int nv=0;for(int i=1;i<ac&&nv<32;i++){char*e;unsigned long x=strtoul(av[i],&e,0);if(*e){fprintf(stderr,"bad value %s\n",av[i]);return 2;}vals[nv++]=(uint32_t)x;}
 char path[128];snprintf(path,sizeof path,"/proc/%d/maps",pid);FILE*f=fopen(path,"r");if(!f){perror(path);return 2;}
 char line[1024];while(fgets(line,sizeof line,f)){unsigned long a,z,off;char perms[8],rest[512]={0};if(sscanf(line,"%lx-%lx %7s %lx %*s %*s %511[\n]",&a,&z,perms,&off,rest)<4)continue;if(perms[0]!='r'||perms[1]!='w'||z<=a||z-a>64*1024*1024)continue;
  /* The 32-bit RCT image and its private continuation occupy this stable
     low-address window under this Proton build. Avoid Wine/UI allocations. */
  int game=strstr(line,"/RCT.EXE")!=NULL; if(!game && (a < 0x00400000UL || a >= 0x00c50000UL))continue;
  size_t len=(size_t)(z-a), got;uint8_t*buf=malloc(len);if(!buf)continue;struct iovec l={buf,len},r={(void*)a,len};got=process_vm_readv(pid,&l,1,&r,1,0);if(got==len){const int widths[]={1,2,4};for(size_t widx=0;widx<sizeof(widths)/sizeof(widths[0]);widx++){int w=widths[widx];for(size_t i=0;i+w<=got;i++)for(int j=0;j<nv;j++)if(vals[j]!=0&&match(buf,i,vals[j],w))printf("%s width=%d value=%u addr=0x%08lx offset=0x%lx\n",game?"game":"anon",w,vals[j],a+i,(unsigned long)(a+i-0x00400000));}}
  free(buf);
 }
 fclose(f);return 0;
}
