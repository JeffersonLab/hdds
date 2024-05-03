void make_insert_xml(){
  ofstream out("pwo.xml");

  double outer_left_y[40]
    ={-40.836,-38.761,-36.633,-34.531,-32.442,-30.343,-28.262,-26.154,-24.037,
      -21.931,
      -19.844,-17.730, -15.676 ,-13.565,-11.489,-9.413,-7.327,-5.234,-3.112,
      -1.036,
      1.019,3.114,5.202,7.334,9.406,11.574,13.674,15.745,17.84,20.031,
      22.096,24.177,26.284,28.407,30.476,32.587,34.649,36.762,38.854,40.939};
  double outer_left_x[40]
    ={40.718,40.717,40.739,40.743,40.739,40.730,40.720,40.716,40.721,40.696,
      40.686,40.700,40.701,40.685,40.690,40.694,40.723,40.718,40.720,40.722,
      40.720,40.671,40.675,40.691,40.684,40.721,40.723,40.711,40.724,40.706,
      40.702,40.732,40.724,40.703,40.756,40.761,40.766,40.787,40.783,40.744};
  double outer_right_y[40]
    ={-40.705,-38.615,-36.53,-34.377,-32.307,-30.222,-28.122,-26.025,-23.924,
      -21.84,
      -19.733,-17.62, -15.529 ,-13.42,-11.359,-9.268,-7.178,-5.073,-2.992,-0.86,
      1.194,3.3,5.384,7.484,9.569,11.669,13.732,15.808,17.921,19.973,
      22.092,24.169,26.282,28.344,30.461,32.563,34.638,36.751,38.821,40.927};
  double outer_right_x[40]
    ={-40.68,-40.666,-40.694,-40.688,-40.675,-40.690,-40.701,-40.718,-40.706,
      -40.729,
      -40.721,-40.743,-40.732,-40.716,-40.708,-40.724,-40.696,-40.698,-40.689,
      -40.713,
      -40.702,-40.701,-40.7,-40.718,-40.710,-40.691,-40.704,-40.7,-40.693,
      -40.681,
      -40.693,-40.691,-40.678,-40.657,-40.643,-40.638,-40.624,-40.618,-40.635,
      -40.629};
  double inner_left_x[2]={7.308,7.322};
  double inner_left_y[2]={-1.025,1.023};
  double inner_right_x[2]={-3.136,-3.129};
  double inner_right_y[2]={-1.047,1.044};

  double ymid[42],dphi[42];
  for (int i=0;i<40;i++){
    int ncopy=40;
    ymid[i]=0.5*(outer_left_y[i]+outer_right_y[i]);
    double dx=outer_left_x[i]-outer_right_x[i];
    dphi[i]=-180/M_PI*(outer_left_y[i]-outer_right_y[i])/dx;
    dx/=39.; // find module size
    if (i==20 || i==21) ncopy=19;
    
    out << "  <composition name=\"XTrow"<<i<<"\">"<< endl;
    out << "    <mposX volume=\"XTModule\" ncopy=\""<< ncopy
	<< "\" X0=\"" << -outer_left_x[i] << "\" dX=\"" << dx <<"\">" <<endl;
    out << "      <column value=\"0\" step=\"1\"/>" <<endl;
    out << "      <row value=\""<<i<<"\"/>"<<endl;
    out << "    </mposX>" << endl;
    out << "  </composition>" << endl;
  }
  // Handle the right side half-width rows 
  ymid[40]=ymid[20];
  ymid[41]=ymid[21];
  dphi[40]=dphi[20];
  dphi[41]=dphi[21];
  for (int i=0;i<2;i++){
    double dx=-(outer_right_x[20+i]-inner_right_x[i])/18.;
    out << "  <composition name=\"XTrow"<<40+i<<"\">"<< endl;
    out << "    <mposX volume=\"XTModule\" ncopy=\"19\" X0=\""
	<< -inner_right_x[i] << "\" dX=\"" << dx <<"\">" <<endl;
    out << "      <column value=\"21\" step=\"1\"/>" <<endl;
    out << "      <row value=\""<<19+i<<"\"/>"<<endl;
    out << "    </mposX>" << endl;
    out << "  </composition>" << endl;
  }

  out << "  <composition name=\"CrystalECAL\">" << endl;

  for (int i=0;i<42;i++){
    out << "    <posXYZ volume=\"XTrow"<<i<<"\" X_Y_Z=\"0. " << ymid[i] 
	<<" 0.\" rot=\"0 0 " << dphi[i] <<"\"/>" << endl;
  }

  out << "  </composition>" << endl << endl;
  

  out.close();
  
}
