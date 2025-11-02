

'use client';

import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { AnalysisData } from '@/lib/types';
import CompanyOverview from './company-overview';
import MarketAnalysis from './market-analysis';
import BusinessModel from './business-model';
import Financials from './financials';
import RiskAnalysis from './risk-analysis';
import Chatbot from './chatbot';
import IssuesTab from './issues-tab';
import InterviewInsights from './interview-insights';
import { Briefcase, ShoppingCart, BarChart, Banknote, ShieldAlert, MessageCircle, SlidersHorizontal, Loader2, FileArchive, FileText, Video, Mic, Type, CalendarPlus, AlertTriangle, MessageSquareQuote } from 'lucide-react';
import { Button } from './ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog"
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Badge } from './ui/badge';
import { useToast } from '@/hooks/use-toast';

type AnalysisDashboardProps = {
  analysisData: AnalysisData;
  startupId: string;
};

type Weightages = {
    teamStrength: number;
    marketOpportunity: number;
    traction: number;
    claimCredibility: number;
    financialHealth: number;
};

const NoDataComponent = ({ onGenerateClick }: { onGenerateClick: () => void }) => (
    <div className="text-center py-20 border-2 border-dashed rounded-lg">
        <h2 className="text-2xl font-headline font-semibold">Analysis data is not available.</h2>
        <p className="text-muted-foreground mt-2">The analysis for this startup might still be in progress or has failed. You can generate a summary.</p>
        <Button onClick={onGenerateClick} className="mt-4">
            <SlidersHorizontal className="mr-2 h-4 w-4" />
            Generate Summary
        </Button>
    </div>
);

export default function AnalysisDashboard({ analysisData: initialAnalysisData, startupId }: AnalysisDashboardProps) {
  const [analysisData, setAnalysisData] = useState(initialAnalysisData);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [isSettingMeeting, setIsSettingMeeting] = useState(false);
  const [isCustomizeDialogOpen, setIsCustomizeDialogOpen] = useState(false);
  const [isMeetingDialogOpen, setIsMeetingDialogOpen] = useState(false);
  const [founderName, setFounderName] = useState('');
  const [founderEmail, setFounderEmail] = useState('');
  const [downloadingFile, setDownloadingFile] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (initialAnalysisData?.metadata?.founder_names?.length > 0) {
      setFounderName(initialAnalysisData.metadata.founder_names[0]);
    }
  }, [initialAnalysisData]);

  const defaultWeights = analysisData?.memo?.draft_v1?._weightage_used;

  const [weights, setWeights] = useState<Weightages>({
    teamStrength: defaultWeights?.team_strength || 20,
    marketOpportunity: defaultWeights?.market_opportunity || 20,
    traction: defaultWeights?.traction || 20,
    claimCredibility: defaultWeights?.claim_credibility || 20,
    financialHealth: defaultWeights?.financial_health || 20,
  });

  const totalWeight = Object.values(weights).reduce((sum, w) => sum + w, 0);

  const handleWeightChange = (key: keyof Weightages, value: number[]) => {
    setWeights(prev => ({...prev, [key]: value[0]}));
  };

  const handleRecalculate = async () => {
    setIsRecalculating(true);
    
    const requestBody = {
      team_strength: weights.teamStrength,
      market_opportunity: weights.marketOpportunity,
      traction: weights.traction,
      claim_credibility: weights.claimCredibility,
      financial_health: weights.financialHealth
    };
    
    console.log('Request Payload:', requestBody);

    try {
      // 1. Call generate_memo endpoint
      const generateMemoResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/generate_memo/${startupId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!generateMemoResponse.ok) {
        const errorData = await generateMemoResponse.json();
        throw new Error(errorData.detail || 'Failed to generate the new memo summary.');
      }
      
      await generateMemoResponse.json();

      // 2. Fetch the updated deal data
      const dealResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/deals/${startupId}`);
      if (!dealResponse.ok) {
        throw new Error('Failed to fetch the updated analysis data.');
      }
      const updatedAnalysisData = await dealResponse.json();
      
      // 3. Update state and close dialog
      setAnalysisData(updatedAnalysisData);
      setIsCustomizeDialogOpen(false);
      
      toast({
        title: "Summary Generated",
        description: "The investment summary has been updated with your new weightages.",
      });

    } catch (error: any) {
      console.error("Failed to recalculate score", error);
      toast({
        variant: "destructive",
        title: "Update Failed",
        description: error.message || "An unexpected error occurred while regenerating the summary.",
      });
    } finally {
      setIsRecalculating(false);
    }
  };

    const handleDownloadSourceFile = async (fileType: 'pitch_deck' | 'video_pitch' | 'audio_pitch' | 'text_notes') => {
        setDownloadingFile(fileType);
        
        let endpoint = '';
        let defaultFilename = '';
        switch (fileType) {
            case 'pitch_deck':
                endpoint = `api/download_pitch_deck/${startupId}`;
                defaultFilename = `${startupId}-pitch-deck.pdf`;
                break;
            case 'video_pitch':
                endpoint = `api/download_video_pitch/${startupId}`;
                defaultFilename = `${startupId}-video-pitch.mp4`;
                break;
            case 'audio_pitch':
                endpoint = `api/download_audio_pitch/${startupId}`;
                defaultFilename = `${startupId}-audio-pitch.mp3`;
                break;
            case 'text_notes':
                endpoint = `api/download_text_notes/${startupId}`;
                defaultFilename = `${startupId}-text-notes.txt`;
                break;
        }

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/${endpoint}`);
            
            if (!response.ok) {
                throw new Error(`Failed to download ${fileType.replace(/_/g, ' ')}.`);
            }

            const blob = await response.blob();
            const contentDisposition = response.headers.get('content-disposition');
            let filename = defaultFilename;
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                if (filenameMatch && filenameMatch.length > 1) {
                    filename = filenameMatch[1];
                }
            }


            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            
            toast({
                title: 'Download Started',
                description: `Your download for ${filename} has started.`,
            });

        } catch (error: any) {
            toast({
                variant: 'destructive',
                title: 'Download Failed',
                description: error.message || 'An unexpected error occurred.',
            });
        } finally {
            setDownloadingFile(null);
        }
    };
    
  const handleSetMeeting = async () => {
    setIsSettingMeeting(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/interviews/initiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deal_id: startupId,
          founder_email: founderEmail,
          founder_name: founderName
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to send interview invitation.');
      }
      
      if (result.success === false) {
        throw new Error(result.detail || 'Failed to send interview invitation.');
      }

      toast({
        title: 'Invitation Sent',
        description: `An interview invitation has been sent to ${founderName}.`,
      });
      setIsMeetingDialogOpen(false); // Close dialog on success
      setFounderEmail(''); // Reset email field

    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Failed to Set Meeting',
        description: error.message || 'An unexpected error occurred.',
      });
    } finally {
      setIsSettingMeeting(false);
    }
  };


  const memo = analysisData?.memo?.draft_v1;
  const rawFiles = analysisData?.raw_files || {};
  const interview = analysisData?.interview;
  const insights = memo?.interview_insights;

  const showIssuesTab = interview?.status !== 'completed' && interview?.issues && interview.issues.length > 0;
  const showInsightsTab = interview?.status === 'completed' && insights && Object.keys(insights).length > 0;

  const getTabListClassName = () => {
    const baseClass = 'grid w-full h-auto mb-6 grid-cols-2';
    if (showIssuesTab) return `${baseClass} md:grid-cols-7`;
    if (showInsightsTab) return `${baseClass} md:grid-cols-7`;
    return `${baseClass} md:grid-cols-6`;
  };

  return (
    <div className="w-full animate-in fade-in-50 duration-500">
       <div className="flex items-center justify-between mb-4">
        <div>
            {/* Title can go here if needed */}
        </div>
        <div className="flex justify-end gap-4">
            <Dialog>
                <DialogTrigger asChild>
                <Button variant="outline"><FileArchive /> Uploaded Data</Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[525px]">
                    <DialogHeader>
                    <DialogTitle className="font-headline text-2xl flex items-center gap-3"><FileArchive className="w-7 h-7 text-primary"/>Uploaded Data Sources</DialogTitle>
                    <DialogDescription>
                        Download the original source files used for this analysis.
                    </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {rawFiles.pitch_deck_url && (
                            <div className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <FileText className="w-6 h-6 text-muted-foreground" />
                                    <span className="font-medium">pitch_deck.pdf</span>
                                </div>
                                <Button size="sm" onClick={() => handleDownloadSourceFile('pitch_deck')} disabled={downloadingFile === 'pitch_deck'}>
                                    {downloadingFile === 'pitch_deck' ? <Loader2 className="animate-spin" /> : 'Download'}
                                </Button>
                            </div>
                        )}
                        {rawFiles.video_pitch_deck_url && (
                            <div className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <Video className="w-6 h-6 text-muted-foreground" />
                                    <span className="font-medium">founder_interview.mp4</span>
                                </div>
                                <Button size="sm" onClick={() => handleDownloadSourceFile('video_pitch')} disabled={downloadingFile === 'video_pitch'}>
                                {downloadingFile === 'video_pitch' ? <Loader2 className="animate-spin" /> : 'Download'}
                                </Button>
                            </div>
                        )}
                        {rawFiles.audio_pitch_deck_url && (
                            <div className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <Mic className="w-6 h-6 text-muted-foreground" />
                                    <span className="font-medium">demo_walkthrough.mp3</span>
                                </div>
                                <Button size="sm" onClick={() => handleDownloadSourceFile('audio_pitch')} disabled={downloadingFile === 'audio_pitch'}>
                                    {downloadingFile === 'audio_pitch' ? <Loader2 className="animate-spin" /> : 'Download'}
                                </Button>
                            </div>
                        )}
                        {rawFiles.text_pitch_deck_url && (
                            <div className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <Type className="w-6 h-6 text-muted-foreground" />
                                    <span className="font-medium">additional_notes.txt</span>
                                </div>
                                <Button size="sm" onClick={() => handleDownloadSourceFile('text_notes')} disabled={downloadingFile === 'text_notes'}>
                                    {downloadingFile === 'text_notes' ? <Loader2 className="animate-spin" /> : 'Download'}
                                </Button>
                            </div>
                        )}
                    </div>
                </DialogContent>
            </Dialog>
            <Dialog open={isMeetingDialogOpen} onOpenChange={setIsMeetingDialogOpen}>
            <DialogTrigger asChild>
                <Button variant="outline"><CalendarPlus /> Set Meeting</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                <DialogTitle className="font-headline text-2xl flex items-center gap-3"><CalendarPlus className="w-7 h-7 text-primary"/>Set Up Interview</DialogTitle>
                <DialogDescription>
                    Send an interview invitation to the startup founder.
                </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="name" className="text-right">
                    Name
                    </Label>
                    <Input
                    id="name"
                    value={founderName}
                    onChange={(e) => setFounderName(e.target.value)}
                    className="col-span-3"
                    />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="email" className="text-right">
                    Email
                    </Label>
                    <Input
                    id="email"
                    type="email"
                    placeholder="founder@example.com"
                    value={founderEmail}
                    onChange={(e) => setFounderEmail(e.target.value)}
                    className="col-span-3"
                    />
                </div>
                </div>
                <DialogFooter>
                <Button onClick={handleSetMeeting} disabled={isSettingMeeting || !founderName || !founderEmail}>
                    {isSettingMeeting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                    Send Invitation
                </Button>
                </DialogFooter>
            </DialogContent>
            </Dialog>

            <Dialog open={isCustomizeDialogOpen} onOpenChange={setIsCustomizeDialogOpen}>
                <DialogTrigger asChild>
                <Button><SlidersHorizontal /> {memo ? 'Regenerate' : 'Generate'} Summary</Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[625px]">
                <DialogHeader>
                    <DialogTitle className="font-headline text-2xl flex items-center gap-3"><SlidersHorizontal className="w-7 h-7 text-primary"/>Customize Score Weightage</DialogTitle>
                    <DialogDescription>
                    Adjust the importance of each factor to recalculate the safety score. The total must be 100%.
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-6 py-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                    {(Object.keys(weights) as Array<keyof Weightages>).map(key => (
                        <div key={key} className="grid gap-2">
                            <div className="flex justify-between">
                                <Label htmlFor={key} className="capitalize">{key.replace(/([A-Z])/g, ' $1')}</Label>
                                <span className="text-sm font-medium">{weights[key]}%</span>
                            </div>
                            <Slider id={key} value={[weights[key]]} onValueChange={(val) => handleWeightChange(key, val)} max={100} step={5} />
                        </div>
                    ))}
                    </div>
                    <div className="flex items-center justify-end">
                        <div className="flex items-center gap-2">
                            <Label>Total Weight:</Label>
                            <Badge variant={totalWeight === 100 ? 'default' : 'destructive'}>{totalWeight}%</Badge>
                        </div>
                    </div>
                </div>
                <DialogFooter>
                    <DialogClose asChild>
                        <Button variant="ghost">Close</Button>
                    </DialogClose>
                    <Button onClick={handleRecalculate} disabled={totalWeight !== 100 || isRecalculating}>
                        {isRecalculating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ShieldAlert className="mr-2 h-4 w-4" />}
                        {isRecalculating ? 'Recalculating...' : 'Generate Summary'}
                    </Button>
                </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
      </div>
      
      <Tabs defaultValue="overview">
        <TabsList className={getTabListClassName()}>
          <TabsTrigger value="overview" className="h-12"><Briefcase className="mr-2"/>Overview</TabsTrigger>
          <TabsTrigger value="market" className="h-12"><ShoppingCart className="mr-2"/>Market</TabsTrigger>
          <TabsTrigger value="model" className="h-12"><BarChart className="mr-2"/>Business Model</TabsTrigger>
          <TabsTrigger value="financials" className="h-12"><Banknote className="mr-2"/>Financials</TabsTrigger>
          <TabsTrigger value="risks" className="h-12"><ShieldAlert className="mr-2"/>Risks</TabsTrigger>
          {showIssuesTab && (
            <TabsTrigger value="issues" className="h-12 text-destructive"><AlertTriangle className="mr-2"/>Issues</TabsTrigger>
          )}
          {showInsightsTab && (
            <TabsTrigger value="insights" className="h-12 text-primary"><MessageSquareQuote className="mr-2"/>Insights</TabsTrigger>
          )}
          <TabsTrigger value="chatbot" className="h-12"><MessageCircle className="mr-2"/>Chatbot</TabsTrigger>
        </TabsList>
        <TabsContent value="overview">
          {memo ? <CompanyOverview data={memo.company_overview} /> : <NoDataComponent onGenerateClick={() => setIsCustomizeDialogOpen(true)} />}
        </TabsContent>
        <TabsContent value="market">
          {memo ? <MarketAnalysis data={memo.market_analysis} publicData={analysisData.public_data} /> : <NoDataComponent onGenerateClick={() => setIsCustomizeDialogOpen(true)} />}
        </TabsContent>
        <TabsContent value="model">
          {memo ? <BusinessModel data={memo.business_model} dealId={startupId}/> : <NoDataComponent onGenerateClick={() => setIsCustomizeDialogOpen(true)} />}
        </TabsContent>
        <TabsContent value="financials">
          {memo ? <Financials data={memo.financials} claims={memo.claims_analysis}/> : <NoDataComponent onGenerateClick={() => setIsCustomizeDialogOpen(true)} />}
        </TabsContent>
        <TabsContent value="risks">
          {memo ? <RiskAnalysis riskMetrics={memo.risk_metrics} conclusion={memo.conclusion} risksAndMitigation={memo.risks_and_mitigation} isRecalculating={isRecalculating} /> : <NoDataComponent onGenerateClick={() => setIsCustomizeDialogOpen(true)} />}
        </TabsContent>
        {showIssuesTab && (
            <TabsContent value="issues">
              {interview ? <IssuesTab issues={interview.issues} /> : <NoDataComponent onGenerateClick={() => {}} />}
            </TabsContent>
        )}
        {showInsightsTab && (
            <TabsContent value="insights">
              {insights ? <InterviewInsights insights={insights} /> : <NoDataComponent onGenerateClick={() => {}} />}
            </TabsContent>
        )}
        <TabsContent value="chatbot">
          {memo ? <Chatbot analysisData={analysisData} /> : <NoDataComponent onGenerateClick={() => setIsCustomizeDialogOpen(true)} />}
        </TabsContent>
      </Tabs>
    </div>
  );

}

    