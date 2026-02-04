import { useState, useEffect, useCallback, useRef } from 'react';
import {
    Upload,
    FileText,
    File,
    FileSpreadsheet,
    FileJson,
    Trash2,
    Search,
    X,
    CheckCircle2,
    Clock,
    Grid3X3,
    List,
} from 'lucide-react';
import { Card, CardContent, Button, Input, Badge, Modal } from '../components/ui';
import { clsx } from 'clsx';
import api from '../services/api';

interface Document {
    id: string;
    filename: string;
    file_type: string;
    size_bytes: number;
    uploaded_at: string;
    chunk_count: number;
    status: string;
}

const getFileIcon = (fileType: string) => {
    switch (fileType.toLowerCase()) {
        case '.pdf':
            return FileText;
        case '.csv':
            return FileSpreadsheet;
        case '.json':
            return FileJson;
        default:
            return File;
    }
};

const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
};

const Documents = () => {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [deleteModalDoc, setDeleteModalDoc] = useState<Document | null>(null);

    const fetchDocuments = async () => {
        try {
            const response = await api.get('/documents/');
            setDocuments(response.data.documents || []);
        } catch (error) {
            console.error('Failed to fetch documents:', error);
            // Mock data for demo
            setDocuments([
                { id: '1', filename: 'sales_report.pdf', file_type: '.pdf', size_bytes: 245600, uploaded_at: new Date().toISOString(), chunk_count: 12, status: 'processed' },
                { id: '2', filename: 'customer_data.csv', file_type: '.csv', size_bytes: 1234567, uploaded_at: new Date().toISOString(), chunk_count: 45, status: 'processed' },
                { id: '3', filename: 'quarterly_review.pdf', file_type: '.pdf', size_bytes: 567890, uploaded_at: new Date().toISOString(), chunk_count: 28, status: 'processed' },
                { id: '4', filename: 'metrics.json', file_type: '.json', size_bytes: 12345, uploaded_at: new Date().toISOString(), chunk_count: 5, status: 'processing' },
            ]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const files = Array.from(e.dataTransfer.files);
            setSelectedFiles((prev) => [...prev, ...files]);
            setShowUploadModal(true);
        }
    }, []);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const files = Array.from(e.target.files);
            setSelectedFiles((prev) => [...prev, ...files]);
            setShowUploadModal(true);
        }
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) return;
        setUploading(true);

        try {
            for (const file of selectedFiles) {
                const formData = new FormData();
                formData.append('file', file);

                await api.post('/documents/upload', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                });
            }

            await fetchDocuments();
            setShowUploadModal(false);
            setSelectedFiles([]);
        } catch (error) {
            console.error('Upload failed:', error);
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (doc: Document) => {
        try {
            await api.delete(`/documents/${doc.id}`);
            setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
            setDeleteModalDoc(null);
        } catch (error) {
            console.error('Delete failed:', error);
        }
    };

    const filteredDocuments = documents.filter((doc) =>
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
                    <p className="text-muted-foreground">Loading documents...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">Documents</h1>
                    <p className="text-muted-foreground mt-1">Upload and manage your knowledge base</p>
                </div>
                <Button onClick={() => setShowUploadModal(true)} icon={<Upload className="w-4 h-4" />}>
                    Upload
                </Button>
            </div>

            {/* Search and Filter */}
            <div className="flex items-center gap-4">
                <div className="flex-1 max-w-md">
                    <Input
                        placeholder="Search documents..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        icon={<Search className="w-4 h-4" />}
                    />
                </div>
                <div className="flex items-center gap-2 border border-border rounded-lg p-1">
                    <button
                        onClick={() => setViewMode('grid')}
                        className={clsx(
                            'p-2 rounded-md transition-colors',
                            viewMode === 'grid' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground'
                        )}
                    >
                        <Grid3X3 className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setViewMode('list')}
                        className={clsx(
                            'p-2 rounded-md transition-colors',
                            viewMode === 'list' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground'
                        )}
                    >
                        <List className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Upload Drop Zone */}
            <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={clsx(
                    'border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200',
                    dragActive
                        ? 'border-primary bg-primary/10'
                        : 'border-border hover:border-primary/50 hover:bg-muted/50'
                )}
            >
                <Upload
                    className={clsx(
                        'w-12 h-12 mx-auto mb-4',
                        dragActive ? 'text-primary' : 'text-muted-foreground'
                    )}
                />
                <p className="text-foreground font-medium mb-1">
                    {dragActive ? 'Drop files here' : 'Drag and drop files here'}
                </p>
                <p className="text-sm text-muted-foreground mb-4">or click to browse</p>
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.txt,.csv,.docx,.json"
                    onChange={handleFileSelect}
                    className="hidden"
                />
                <Button
                    variant="outline"
                    className="cursor-pointer"
                    onClick={() => fileInputRef.current?.click()}
                >
                    Select Files
                </Button>
                <p className="text-xs text-muted-foreground mt-4">
                    Supported: PDF, TXT, CSV, DOCX, JSON (Max 10MB)
                </p>
            </div>

            {/* Documents Grid/List */}
            {filteredDocuments.length === 0 ? (
                <Card>
                    <CardContent className="py-12 text-center">
                        <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                        <h3 className="text-lg font-medium text-foreground mb-2">No documents found</h3>
                        <p className="text-muted-foreground">
                            {searchQuery
                                ? 'Try a different search term'
                                : 'Upload your first document to get started'}
                        </p>
                    </CardContent>
                </Card>
            ) : viewMode === 'grid' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {filteredDocuments.map((doc) => {
                        const Icon = getFileIcon(doc.file_type);
                        return (
                            <Card key={doc.id} hover className="group">
                                <CardContent>
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20">
                                            <Icon className="w-6 h-6 text-violet-400" />
                                        </div>
                                        <button
                                            onClick={() => setDeleteModalDoc(doc)}
                                            className="p-2 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                    <h4 className="font-medium text-foreground truncate mb-1" title={doc.filename}>
                                        {doc.filename}
                                    </h4>
                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                        <span>{formatFileSize(doc.size_bytes)}</span>
                                        <span>•</span>
                                        <span>{doc.chunk_count} chunks</span>
                                    </div>
                                    <div className="flex items-center justify-between mt-3">
                                        <Badge
                                            variant={(doc.status === 'processed' || doc.status === 'indexed') ? 'success' : 'warning'}
                                            size="sm"
                                        >
                                            {(doc.status === 'processed' || doc.status === 'indexed') ? (
                                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                            ) : (
                                                <Clock className="w-3 h-3 mr-1" />
                                            )}
                                            {doc.status}
                                        </Badge>
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })}
                </div>
            ) : (
                <Card>
                    <div className="divide-y divide-border">
                        {filteredDocuments.map((doc) => {
                            const Icon = getFileIcon(doc.file_type);
                            return (
                                <div
                                    key={doc.id}
                                    className="flex items-center gap-4 p-4 hover:bg-muted/50 transition-colors group"
                                >
                                    <div className="p-2.5 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20">
                                        <Icon className="w-5 h-5 text-violet-400" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-medium text-foreground truncate">
                                            {doc.filename}
                                        </h4>
                                        <p className="text-sm text-muted-foreground">
                                            {formatFileSize(doc.size_bytes)} • {doc.chunk_count} chunks • {formatDate(doc.uploaded_at)}
                                        </p>
                                    </div>
                                    <Badge variant={(doc.status === 'processed' || doc.status === 'indexed') ? 'success' : 'warning'} size="sm">
                                        {doc.status}
                                    </Badge>
                                    <button
                                        onClick={() => setDeleteModalDoc(doc)}
                                        className="p-2 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </Card>
            )}

            {/* Upload Modal */}
            <Modal
                isOpen={showUploadModal}
                onClose={() => {
                    setShowUploadModal(false);
                    setSelectedFiles([]);
                }}
                title="Upload Documents"
                size="md"
            >
                <div className="space-y-4">
                    {selectedFiles.length > 0 ? (
                        <>
                            <div className="space-y-2 max-h-60 overflow-y-auto">
                                {selectedFiles.map((file, idx) => (
                                    <div
                                        key={idx}
                                        className="flex items-center justify-between p-3 rounded-lg bg-muted"
                                    >
                                        <div className="flex items-center gap-3">
                                            <FileText className="w-5 h-5 text-violet-400" />
                                            <div>
                                                <p className="text-sm font-medium text-foreground">{file.name}</p>
                                                <p className="text-xs text-muted-foreground">
                                                    {formatFileSize(file.size)}
                                                </p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() =>
                                                setSelectedFiles((prev) => prev.filter((_, i) => i !== idx))
                                            }
                                            className="p-1.5 rounded-lg hover:bg-background text-muted-foreground hover:text-foreground transition-colors"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                            <div className="flex justify-end gap-3">
                                <Button
                                    variant="outline"
                                    onClick={() => {
                                        setShowUploadModal(false);
                                        setSelectedFiles([]);
                                    }}
                                >
                                    Cancel
                                </Button>
                                <Button onClick={handleUpload} loading={uploading}>
                                    Upload {selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''}
                                </Button>
                            </div>
                        </>
                    ) : (
                        <div className="text-center py-8">
                            <Upload className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                            <p className="text-muted-foreground">No files selected</p>
                            <input
                                type="file"
                                multiple
                                accept=".pdf,.txt,.csv,.docx,.json"
                                onChange={handleFileSelect}
                                className="hidden"
                                id="modal-file-upload"
                            />
                            <label htmlFor="modal-file-upload">
                                <Button variant="outline" className="mt-4 cursor-pointer">
                                    Select Files
                                </Button>
                            </label>
                        </div>
                    )}
                </div>
            </Modal>

            {/* Delete Confirmation Modal */}
            <Modal
                isOpen={!!deleteModalDoc}
                onClose={() => setDeleteModalDoc(null)}
                title="Delete Document"
                size="sm"
            >
                <div className="space-y-4">
                    <p className="text-muted-foreground">
                        Are you sure you want to delete <strong className="text-foreground">{deleteModalDoc?.filename}</strong>? This action cannot be undone.
                    </p>
                    <div className="flex justify-end gap-3">
                        <Button variant="outline" onClick={() => setDeleteModalDoc(null)}>
                            Cancel
                        </Button>
                        <Button variant="destructive" onClick={() => deleteModalDoc && handleDelete(deleteModalDoc)}>
                            Delete
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default Documents;
